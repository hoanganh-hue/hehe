/**
 * Jest Setup for Frontend Testing
 * Configures test environment and global utilities
 */

// Mock fetch API for testing
global.fetch = jest.fn();

// Mock localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};
global.localStorage = localStorageMock;

// Mock sessionStorage
const sessionStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};
global.sessionStorage = sessionStorageMock;

// Mock window.location
delete global.window.location;
global.window.location = {
  href: '',
  pathname: '/',
  search: '',
  hash: '',
  reload: jest.fn(),
  assign: jest.fn(),
  replace: jest.fn(),
};

// Mock window.history
global.window.history = {
  pushState: jest.fn(),
  replaceState: jest.fn(),
  back: jest.fn(),
  forward: jest.fn(),
  go: jest.fn(),
};

// Mock matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(), // deprecated
    removeListener: jest.fn(), // deprecated
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
});

// Mock ResizeObserver
global.ResizeObserver = jest.fn().mockImplementation(() => ({
  observe: jest.fn(),
  unobserve: jest.fn(),
  disconnect: jest.fn(),
}));

// Mock IntersectionObserver
global.IntersectionObserver = jest.fn().mockImplementation(() => ({
  observe: jest.fn(),
  unobserve: jest.fn(),
  disconnect: jest.fn(),
}));

// Mock console methods for cleaner test output
const originalConsoleError = console.error;
const originalConsoleWarn = console.warn;

beforeAll(() => {
  console.error = jest.fn();
  console.warn = jest.fn();
});

afterAll(() => {
  console.error = originalConsoleError;
  console.warn = originalConsoleWarn;
});

// Mock Chart.js if used
jest.mock('chart.js', () => ({
  Chart: jest.fn().mockImplementation(() => ({
    update: jest.fn(),
    destroy: jest.fn(),
  })),
  register: jest.fn(),
}));

// Mock DOMParser
global.DOMParser = jest.fn().mockImplementation(() => ({
  parseFromString: jest.fn().mockReturnValue({
    documentElement: {
      textContent: '',
    },
  }),
}));

// Setup test utilities
const testUtils = {
  // Create mock DOM element
  createMockElement: (tagName = 'div', attributes = {}) => {
    const element = document.createElement(tagName);
    Object.keys(attributes).forEach(attr => {
      element.setAttribute(attr, attributes[attr]);
    });
    return element;
  },

  // Mock fetch response
  mockFetchResponse: (data, status = 200) => {
    return Promise.resolve({
      ok: status >= 200 && status < 300,
      status,
      json: () => Promise.resolve(data),
      text: () => Promise.resolve(JSON.stringify(data)),
      blob: () => Promise.resolve(new Blob([JSON.stringify(data)])),
    });
  },

  // Mock fetch error
  mockFetchError: (error = 'Network error') => {
    return Promise.reject(new Error(error));
  },

  // Wait for next tick
  nextTick: () => new Promise(resolve => setTimeout(resolve, 0)),

  // Create mock event
  createMockEvent: (type, properties = {}) => {
    const event = new Event(type);
    Object.assign(event, properties);
    return event;
  },

  // Mock API responses
  mockApiResponse: {
    success: (data = {}) => ({
      success: true,
      data,
      message: 'Success',
    }),
    error: (message = 'Error occurred') => ({
      success: false,
      message,
    }),
  },
};

// Make testUtils available globally
global.testUtils = testUtils;

// Custom matchers
expect.extend({
  toBeValidEmail(received) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    const pass = emailRegex.test(received);
    return {
      message: () => `expected ${received} to be a valid email`,
      pass,
    };
  },

  toBeValidPhone(received) {
    const phoneRegex = /^(\+84|84|0)[3|5|7|8|9][0-9]{8}$/;
    const pass = phoneRegex.test(received);
    return {
      message: () => `expected ${received} to be a valid Vietnamese phone number`,
      pass,
    };
  },

  toHaveClass(received, className) {
    const pass = received.classList.contains(className);
    return {
      message: () => `expected element to have class "${className}"`,
      pass,
    };
  },

  toBeVisible(received) {
    const pass = received.style.display !== 'none' && received.style.visibility !== 'hidden';
    return {
      message: () => `expected element to be visible`,
      pass,
    };
  },
});

// Cleanup after each test
afterEach(() => {
  jest.clearAllMocks();
  document.body.innerHTML = '';

  // Reset localStorage/sessionStorage mocks
  localStorageMock.clear();
  sessionStorageMock.clear();

  // Reset window.location
  global.window.location.href = '';
  global.window.location.pathname = '/';
  global.window.location.search = '';
  global.window.location.hash = '';
});

// Global test timeout
jest.setTimeout(10000);

// Export test utilities for use in test files
export { testUtils };