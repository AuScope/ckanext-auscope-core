/*
 * Opt-in FOR/EPSG autocomplete for CKAN forms.
 *
 * The small CommonJS export exists solely so the request, serialization and
 * stale-response behaviour can be tested without adding a frontend dependency.
 */
(function (root, factory) {
  "use strict";

  var api = factory();
  if (typeof module === "object" && module.exports) {
    module.exports = api;
  }
  if (root && root.ckan) {
    api.register(root.ckan);
  }
}(typeof window !== "undefined" ? window : null, function () {
  "use strict";

  function parseOption(value, fallback) {
    if (value === undefined || value === null || value === "") {
      return fallback;
    }
    if (typeof value !== "string") {
      return value;
    }
    try {
      return JSON.parse(value);
    } catch (error) {
      return fallback;
    }
  }

  function asBoolean(value) {
    return value === true || value === "true" || value === 1 || value === "1";
  }

  function displayText(item, vocabulary) {
    if (vocabulary === "epsg") {
      return item.id + " - " + item.label;
    }
    return item.label + " (" + item.id + ")";
  }

  function normalizeItems(items, vocabulary) {
    var seen = {};
    if (!Array.isArray(items)) {
      return [];
    }
    return items.reduce(function (normalized, item) {
      if (!item || typeof item.id !== "string" ||
          typeof item.label !== "string" || seen[item.id]) {
        return normalized;
      }
      seen[item.id] = true;
      normalized.push({
        id: item.id,
        label: item.label,
        text: displayText(item, vocabulary),
        vocabulary: item.vocabulary || "",
        description: item.description || ""
      });
      return normalized;
    }, []);
  }

  function selectionValue(item, source) {
    if (source === "label") {
      return item.label;
    }
    if (source === "display") {
      return item.text;
    }
    if (source === "selection") {
      var selection = {
        id: item.id,
        label: item.label
      };
      if (item.vocabulary) {
        selection.vocabulary = item.vocabulary;
      }
      if (item.description) {
        selection.description = item.description;
      }
      return selection;
    }
    return item.id;
  }

  function serializeSelections(items, source, format) {
    var values = items.map(function (item) {
      return selectionValue(item, source);
    });
    if (format === "json") {
      return JSON.stringify(values);
    }
    if (format === "csv") {
      return values.join(",");
    }
    return values.length ? String(values[0]) : "";
  }

  function createModule($) {
    return {
      options: {
        vocabulary: "for",
        endpoint: "",
        multiple: false,
        initialValues: [],
        placeholder: "Search the vocabulary",
        minimumInputLength: 2,
        limit: 20,
        debounce: 250,
        loadingMessage: "Searching…",
        noResultsMessage: "No matching values found.",
        invalidMessage: "Enter a valid search term.",
        errorMessage: "Vocabulary search is temporarily unavailable. Try again."
      },

      initialize: function () {
        this.input = this.el.find("[data-vocabulary-input]");
        this.status = this.el.find("[data-vocabulary-status]");
        this.outputs = this.el.find("[data-vocabulary-output]");
        this.requestNumber = 0;
        this.pendingRequest = null;
        this.pendingTimer = null;
        this.multiple = asBoolean(this.options.multiple);
        this.minimumInputLength = Math.max(
          1,
          Number(this.options.minimumInputLength) || 1
        );
        this.initialValues = normalizeItems(
          parseOption(this.options.initialValues, []),
          this.options.vocabulary
        );

        this.input.select2({
          placeholder: this.options.placeholder,
          minimumInputLength: this.minimumInputLength,
          multiple: this.multiple,
          allowClear: !this.multiple,
          query: $.proxy(this.query, this)
        });
        this.applyAccessibility();
        this.input.on("change", $.proxy(this.syncOutputs, this));

        if (this.initialValues.length) {
          this.input.select2(
            "data",
            this.multiple ? this.initialValues : this.initialValues[0],
            true
          );
        }
        this.syncOutputs();
      },

      applyAccessibility: function () {
        var labelledBy = this.input.attr("data-label-id");
        var describedBy = this.input.attr("aria-describedby");
        var container = this.input.select2("container");
        container.attr({
          "aria-labelledby": labelledBy,
          "aria-describedby": describedBy
        });
        container.find("input").attr({
          "aria-labelledby": labelledBy,
          "aria-describedby": describedBy
        });
      },

      query: function (query) {
        var self = this;
        var term = $.trim(query.term || "");
        var requestNumber = ++this.requestNumber;

        if (this.pendingTimer) {
          clearTimeout(this.pendingTimer);
        }
        if (this.pendingRequest) {
          this.pendingRequest.abort();
          this.pendingRequest = null;
        }
        var minimumInputLength = this.minimumInputLength || Math.max(
          1,
          Number(this.options.minimumInputLength) || 1
        );
        if (term.length < minimumInputLength) {
          this.setStatus("");
          query.callback({results: [], more: false});
          return;
        }

        this.setStatus(this.options.loadingMessage);
        this.pendingTimer = setTimeout(function () {
          self.pendingTimer = null;
          self.pendingRequest = $.ajax({
            url: self.options.endpoint,
            data: {q: term, limit: Number(self.options.limit)},
            dataType: "json"
          }).done(function (response) {
            if (requestNumber !== self.requestNumber) {
              return;
            }
            var items = normalizeItems(
              response && response.items,
              self.options.vocabulary
            );
            self.setStatus(items.length ? "" : self.options.noResultsMessage);
            query.callback({results: items, more: false});
          }).fail(function (xhr, status) {
            if (status === "abort" || requestNumber !== self.requestNumber) {
              return;
            }
            var message = xhr && xhr.status === 400
              ? self.options.invalidMessage
              : xhr && xhr.status === 404
                ? self.options.noResultsMessage
                : self.options.errorMessage;
            self.setStatus(message);
            query.callback({results: [], more: false});
          }).always(function () {
            if (requestNumber === self.requestNumber) {
              self.pendingRequest = null;
            }
          });
        }, Number(this.options.debounce));
      },

      syncOutputs: function () {
        var selected = this.input.select2("data");
        var items = selected ? (Array.isArray(selected) ? selected : [selected]) : [];
        this.outputs.each(function () {
          var output = $(this);
          output.val(serializeSelections(
            items,
            output.attr("data-value-source") || "id",
            output.attr("data-value-format") || "first"
          ));
        });
      },

      setStatus: function (message) {
        this.status.text(message);
      },

      teardown: function () {
        ++this.requestNumber;
        if (this.pendingTimer) {
          clearTimeout(this.pendingTimer);
        }
        if (this.pendingRequest) {
          this.pendingRequest.abort();
        }
        this.input.off("change");
        this.input.select2("destroy");
      }
    };
  }

  function register(ckan) {
    ckan.module("auscope-core-vocabulary-picker", function ($) {
      return createModule($);
    });
  }

  return {
    createModule: createModule,
    displayText: displayText,
    normalizeItems: normalizeItems,
    parseOption: parseOption,
    serializeSelections: serializeSelections,
    register: register
  };
}));
