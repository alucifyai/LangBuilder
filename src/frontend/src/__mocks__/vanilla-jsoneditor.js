/**
 * Mock for vanilla-jsoneditor
 *
 * This mock is required for Jest testing to avoid ESM/CommonJS compatibility issues.
 * The vanilla-jsoneditor library uses ESM format which causes Jest parse errors.
 */

// Mock JSONEditor class
class JSONEditor {
  constructor(options) {
    this.options = options;
    this.content = { json: {} };
  }

  set(content) {
    this.content = content;
  }

  get() {
    return this.content;
  }

  update(content) {
    this.content = { ...this.content, ...content };
  }

  updateProps(props) {
    this.options = { ...this.options, ...props };
  }

  destroy() {
    // Clean up
  }

  focus() {
    // No-op in mock
  }

  refresh() {
    // No-op in mock
  }
}

// Export the mock JSONEditor class
module.exports = {
  JSONEditor,
  __esModule: true,
  default: {
    JSONEditor,
  },
};
