/*
 * Opt-in vocabulary and ROR autocomplete for CKAN forms.
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

  var nextControlId = 0;

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
    if (vocabulary === "ror" && item.description) {
      return item.label + " (" + item.description + ") — " + item.id;
    }
    if (vocabulary === "ror" && !item.label) {
      return item.id;
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

        this.mountSelect();
        this.applyAccessibility();
        this.syncOutputs();
        this.bindCompositeLifecycle();
      },

      mountSelect: function () {
        var self = this;
        this.select = $("<select>").attr({
          id: "auscope-core-vocabulary-control-" + (++nextControlId),
          "aria-required": this.input.prop("required") ? "true" : null
        }).prop("multiple", this.multiple).insertAfter(this.input);
        if (!this.multiple) {
          this.select.append(new Option("", ""));
        }
        this.initialValues.forEach(function (item) {
          self.select.append(new Option(item.text, item.id, true, true));
        });

        this.select.select2({
          width: "100%",
          placeholder: this.options.placeholder,
          allowClear: !this.multiple,
          ajax: {
            transport: function (params, success) {
              self.query({
                term: params.data.term,
                callback: function (data) {
                  success({results: data.results, pagination: {more: false}});
                }
              });
              return {abort: self.cancelSearch.bind(self)};
            }
          }
        });
        this.widget = this.select.data("select2");
        this.select.on("change.auscopeCoreVocabulary", this.syncOutputs.bind(this));
      },

      bindCompositeLifecycle: function () {
        this.composite = this.el.closest('[data-module~="auscope-composite"]');
        if (!this.composite.length) {
          return;
        }
        var row = this.el.closest("[data-composite-row]")[0];
        this.onReindexed = this.applyAccessibility.bind(this);
        this.onCleared = $.proxy(function (_event, detail) {
          if (detail.row[0] === row) {
            this.cancelSearch();
            this.setStatus("");
            this.select.val(null).trigger("change");
          }
        }, this);
        this.onRemoved = $.proxy(function (_event, detail) {
          if (detail.row[0] === row) {
            this.teardown();
          }
        }, this);
        this.composite.on("auscope-composite:rows-reindexed", this.onReindexed);
        this.composite.on("auscope-composite:row-cleared", this.onCleared);
        this.composite.on("auscope-composite:row-removed", this.onRemoved);
      },

      applyAccessibility: function () {
        var label = this.el.find("[data-vocabulary-label]");
        label.attr("for", this.select.attr("id"));
        var labelledBy = label.attr("id");
        var describedBy = this.el.find("[data-vocabulary-description]").map(function () {
          return this.id;
        }).get().join(" ");
        var attributes = {
          "aria-labelledby": labelledBy,
          "aria-describedby": describedBy,
          "aria-invalid": this.input.attr("aria-invalid")
        };
        this.input.attr(attributes).attr("data-label-id", labelledBy);
        var selection = this.select.next(".select2-container").find(".select2-selection");
        selection.attr(attributes).attr("aria-required", this.select.attr("aria-required"));
      },

      query: function (query) {
        var self = this;
        var term = $.trim(query.term || "");
        this.cancelSearch();
        var requestNumber = this.requestNumber;
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
        var saved = this.initialValues;
        var items = this.select.select2("data").filter(function (item) {
          return item.id;
        }).map(function (item) {
          if (typeof item.label === "string") {
            return item;
          }
          return saved.find(function (initial) {
            return initial.id === item.id;
          }) || item;
        });
        this.input.val(serializeSelections(items, "id", this.multiple ? "csv" : "first"));
        this.outputs.each(function () {
          var output = $(this);
          output.val(serializeSelections(
            items,
            output.attr("data-value-source") || "id",
            output.attr("data-value-format") || "first"
          ));
        });
        this.input.trigger("change");
      },

      setStatus: function (message) {
        this.status.text(message);
      },

      cancelSearch: function () {
        ++this.requestNumber;
        if (this.pendingTimer) {
          clearTimeout(this.pendingTimer);
          this.pendingTimer = null;
        }
        if (this.pendingRequest) {
          this.pendingRequest.abort();
          this.pendingRequest = null;
        }
      },

      teardown: function () {
        this.cancelSearch();
        if (this.composite && this.composite.length) {
          this.composite.off("auscope-composite:rows-reindexed", this.onReindexed);
          this.composite.off("auscope-composite:row-cleared", this.onCleared);
          this.composite.off("auscope-composite:row-removed", this.onRemoved);
        }
        if (this.widget) {
          this.select.off(".auscopeCoreVocabulary");
          this.widget.destroy();
          this.select.remove();
          this.widget = null;
        }
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
