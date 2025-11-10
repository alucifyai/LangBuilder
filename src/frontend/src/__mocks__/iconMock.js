// Mock for icon components
import React from "react";

module.exports = {
  BotMessageSquareIcon: React.forwardRef((props, ref) =>
    React.createElement("svg", { ...props, ref, "data-testid": "mock-icon" })
  ),
};
