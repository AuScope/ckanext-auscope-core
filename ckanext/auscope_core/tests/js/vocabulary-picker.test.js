"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");

const picker = require("../../assets/js/vocabulary-picker.js");

function deferredRequest() {
  const handlers = {done: [], fail: [], always: []};
  return {
    aborted: false,
    done(callback) {
      handlers.done.push(callback);
      return this;
    },
    fail(callback) {
      handlers.fail.push(callback);
      return this;
    },
    always(callback) {
      handlers.always.push(callback);
      return this;
    },
    abort() {
      this.aborted = true;
    },
    resolve(value) {
      handlers.done.forEach((callback) => callback(value));
      handlers.always.forEach((callback) => callback());
    },
    reject(xhr, status = "error") {
      handlers.fail.forEach((callback) => callback(xhr, status));
      handlers.always.forEach((callback) => callback());
    }
  };
}

function queryHarness(overrides = {}) {
  const requests = [];
  const statuses = [];
  const $ = {
    trim: (value) => value.trim(),
    ajax: (options) => {
      const request = deferredRequest();
      request.options = options;
      requests.push(request);
      return request;
    }
  };
  const instance = picker.createModule($);
  instance.options = Object.assign({
    vocabulary: "for",
    endpoint: "/api/auscope-core/v1/vocabularies/for",
    minimumInputLength: 2,
    limit: 10,
    debounce: 0,
    loadingMessage: "Searching…",
    noResultsMessage: "No matching values found.",
    invalidMessage: "Enter a valid search term.",
    errorMessage: "Vocabulary search is temporarily unavailable. Try again."
  }, overrides);
  instance.requestNumber = 0;
  instance.pendingRequest = null;
  instance.pendingTimer = null;
  instance.status = {text: (message) => statuses.push(message)};
  return {instance, requests, statuses};
}

function waitForTimer() {
  return new Promise((resolve) => setTimeout(resolve, 5));
}

test("normalizes FOR and EPSG results and removes duplicate identifiers", () => {
  const items = [
    {id: "3705", label: "Geology", vocabulary: "FOR"},
    {id: "3705", label: "Duplicate"},
    {id: 4326, label: "Invalid non-string identifier"}
  ];
  assert.deepEqual(picker.normalizeItems(items, "for"), [{
    id: "3705",
    label: "Geology",
    text: "Geology (3705)",
    vocabulary: "FOR",
    description: ""
  }]);
  assert.equal(
    picker.normalizeItems([{id: "4326", label: "WGS 84"}], "epsg")[0].text,
    "4326 - WGS 84"
  );
});

test("serializes single, multiple, removal, labels and normalized selections", () => {
  const selections = picker.normalizeItems([
    {id: "3705", label: "Geology", vocabulary: "FOR"},
    {id: "3706", label: "Geophysics", vocabulary: "FOR"}
  ], "for");
  assert.equal(picker.serializeSelections(selections, "id", "csv"), "3705,3706");
  assert.equal(picker.serializeSelections(selections, "display", "first"), "Geology (3705)");
  assert.equal(
    picker.serializeSelections(selections, "label", "json"),
    '["Geology","Geophysics"]'
  );
  assert.deepEqual(
    JSON.parse(picker.serializeSelections(selections, "selection", "json")),
    [
      {id: "3705", label: "Geology", vocabulary: "FOR"},
      {id: "3706", label: "Geophysics", vocabulary: "FOR"}
    ]
  );
  assert.equal(picker.serializeSelections([], "id", "csv"), "");
  assert.equal(picker.serializeSelections([], "selection", "json"), "[]");
});

test("preserves complete edit values for a form round trip", () => {
  const encoded = JSON.stringify([{id: "4326", label: "WGS 84"}]);
  const decoded = picker.parseOption(encoded, []);
  const normalized = picker.normalizeItems(decoded, "epsg");
  assert.equal(normalized[0].id, "4326");
  assert.equal(normalized[0].label, "WGS 84");
  assert.equal(normalized[0].text, "4326 - WGS 84");
});

test("search maps normalized API items and always disables pagination", async () => {
  const {instance, requests, statuses} = queryHarness();
  let result;
  instance.query({term: "geo", callback: (value) => { result = value; }});
  await waitForTimer();
  assert.deepEqual(requests[0].options.data, {q: "geo", limit: 10});
  requests[0].resolve({items: [{id: "3705", label: "Geology"}]});
  assert.equal(result.results[0].id, "3705");
  assert.equal(result.more, false);
  assert.deepEqual(statuses, ["Searching…", ""]);
});

test("empty and invalid API result sets become a safe no-results response", async () => {
  for (const response of [{items: []}, {items: "invalid"}, {}]) {
    const {instance, requests, statuses} = queryHarness();
    let result;
    instance.query({term: "none", callback: (value) => { result = value; }});
    await waitForTimer();
    requests[0].resolve(response);
    assert.deepEqual(result, {results: [], more: false});
    assert.equal(statuses.at(-1), "No matching values found.");
  }
});

test("invalid queries and provider failures show non-technical feedback", async () => {
  for (const [statusCode, message] of [
    [400, "Enter a valid search term."],
    [404, "No matching values found."],
    [502, "Vocabulary search is temporarily unavailable. Try again."],
    [503, "Vocabulary search is temporarily unavailable. Try again."]
  ]) {
    const {instance, requests, statuses} = queryHarness();
    let result;
    instance.query({term: "geology", callback: (value) => { result = value; }});
    await waitForTimer();
    requests[0].reject({status: statusCode});
    assert.deepEqual(result, {results: [], more: false});
    assert.equal(statuses.at(-1), message);
  }
});

test("short searches do not make a request", () => {
  const {instance, requests} = queryHarness({minimumInputLength: 3});
  let result;
  instance.query({term: "ab", callback: (value) => { result = value; }});
  assert.deepEqual(result, {results: [], more: false});
  assert.equal(requests.length, 0);
});

test("new searches abort old requests and ignore out-of-order responses", async () => {
  const {instance, requests} = queryHarness();
  const callbacks = [];
  instance.query({term: "geo", callback: (value) => callbacks.push(["old", value])});
  await waitForTimer();
  instance.query({term: "geol", callback: (value) => callbacks.push(["new", value])});
  await waitForTimer();
  assert.equal(requests[0].aborted, true);

  requests[1].resolve({items: [{id: "3705", label: "Geology"}]});
  requests[0].resolve({items: [{id: "37", label: "Old result"}]});
  assert.equal(callbacks.length, 1);
  assert.equal(callbacks[0][0], "new");
  assert.equal(callbacks[0][1].results[0].id, "3705");
});

test("ROR selection keeps canonical URL and displays the saved name or ID", () => {
  const id = "https://ror.org/01nfmeh72";
  const [result] = picker.normalizeItems(
    [{id, label: "Research University", description: "Australia"}], "ror"
  );
  assert.match(result.text, /Research University.*Australia/);
  assert.equal(picker.serializeSelections([result], "id", "first"), id);
  assert.equal(picker.serializeSelections([result], "label", "first"), "Research University");
  const saved = picker.normalizeItems([{id, label: ""}], "ror");
  assert.equal(saved[0].text, id);
  assert.equal(picker.serializeSelections(saved, "label", "first"), "");
});
