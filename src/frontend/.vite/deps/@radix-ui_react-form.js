import {
  require_react_dom
} from "./chunk-B6BVOBJQ.js";
import {
  require_react
} from "./chunk-YHBWKRJN.js";
import {
  __toESM
} from "./chunk-VHXUCOYC.js";

// node_modules/@babel/runtime/helpers/esm/extends.js
function _extends() {
  return _extends = Object.assign ? Object.assign.bind() : function(n) {
    for (var e = 1; e < arguments.length; e++) {
      var t = arguments[e];
      for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]);
    }
    return n;
  }, _extends.apply(null, arguments);
}

// node_modules/@radix-ui/react-form/dist/index.mjs
var import_react7 = __toESM(require_react(), 1);

// node_modules/@radix-ui/react-form/node_modules/@radix-ui/primitive/dist/index.mjs
function $e42e1063c40fb3ef$export$b9ecd428b558ff10(originalEventHandler, ourEventHandler, { checkForDefaultPrevented = true } = {}) {
  return function handleEvent(event) {
    originalEventHandler === null || originalEventHandler === void 0 || originalEventHandler(event);
    if (checkForDefaultPrevented === false || !event.defaultPrevented) return ourEventHandler === null || ourEventHandler === void 0 ? void 0 : ourEventHandler(event);
  };
}

// node_modules/@radix-ui/react-form/node_modules/@radix-ui/react-compose-refs/dist/index.mjs
var import_react = __toESM(require_react(), 1);
function $6ed0406888f73fc4$var$setRef(ref, value) {
  if (typeof ref === "function") ref(value);
  else if (ref !== null && ref !== void 0) ref.current = value;
}
function $6ed0406888f73fc4$export$43e446d32b3d21af(...refs) {
  return (node) => refs.forEach(
    (ref) => $6ed0406888f73fc4$var$setRef(ref, node)
  );
}
function $6ed0406888f73fc4$export$c7b2cbe3552a0d05(...refs) {
  return (0, import_react.useCallback)($6ed0406888f73fc4$export$43e446d32b3d21af(...refs), refs);
}

// node_modules/@radix-ui/react-form/node_modules/@radix-ui/react-context/dist/index.mjs
var import_react2 = __toESM(require_react(), 1);
function $c512c27ab02ef895$export$50c7b4e9d9f19c1(scopeName, createContextScopeDeps = []) {
  let defaultContexts = [];
  function $c512c27ab02ef895$export$fd42f52fd3ae1109(rootComponentName, defaultContext) {
    const BaseContext = (0, import_react2.createContext)(defaultContext);
    const index = defaultContexts.length;
    defaultContexts = [
      ...defaultContexts,
      defaultContext
    ];
    function Provider(props) {
      const { scope, children, ...context } = props;
      const Context = (scope === null || scope === void 0 ? void 0 : scope[scopeName][index]) || BaseContext;
      const value = (0, import_react2.useMemo)(
        () => context,
        Object.values(context)
      );
      return (0, import_react2.createElement)(Context.Provider, {
        value
      }, children);
    }
    function useContext(consumerName, scope) {
      const Context = (scope === null || scope === void 0 ? void 0 : scope[scopeName][index]) || BaseContext;
      const context = (0, import_react2.useContext)(Context);
      if (context) return context;
      if (defaultContext !== void 0) return defaultContext;
      throw new Error(`\`${consumerName}\` must be used within \`${rootComponentName}\``);
    }
    Provider.displayName = rootComponentName + "Provider";
    return [
      Provider,
      useContext
    ];
  }
  const createScope = () => {
    const scopeContexts = defaultContexts.map((defaultContext) => {
      return (0, import_react2.createContext)(defaultContext);
    });
    return function useScope(scope) {
      const contexts = (scope === null || scope === void 0 ? void 0 : scope[scopeName]) || scopeContexts;
      return (0, import_react2.useMemo)(
        () => ({
          [`__scope${scopeName}`]: {
            ...scope,
            [scopeName]: contexts
          }
        }),
        [
          scope,
          contexts
        ]
      );
    };
  };
  createScope.scopeName = scopeName;
  return [
    $c512c27ab02ef895$export$fd42f52fd3ae1109,
    $c512c27ab02ef895$var$composeContextScopes(createScope, ...createContextScopeDeps)
  ];
}
function $c512c27ab02ef895$var$composeContextScopes(...scopes) {
  const baseScope = scopes[0];
  if (scopes.length === 1) return baseScope;
  const createScope1 = () => {
    const scopeHooks = scopes.map(
      (createScope) => ({
        useScope: createScope(),
        scopeName: createScope.scopeName
      })
    );
    return function useComposedScopes(overrideScopes) {
      const nextScopes1 = scopeHooks.reduce((nextScopes, { useScope, scopeName }) => {
        const scopeProps = useScope(overrideScopes);
        const currentScope = scopeProps[`__scope${scopeName}`];
        return {
          ...nextScopes,
          ...currentScope
        };
      }, {});
      return (0, import_react2.useMemo)(
        () => ({
          [`__scope${baseScope.scopeName}`]: nextScopes1
        }),
        [
          nextScopes1
        ]
      );
    };
  };
  createScope1.scopeName = baseScope.scopeName;
  return createScope1;
}

// node_modules/@radix-ui/react-form/node_modules/@radix-ui/react-id/dist/index.mjs
var $2AODx$react = __toESM(require_react(), 1);

// node_modules/@radix-ui/react-form/node_modules/@radix-ui/react-use-layout-effect/dist/index.mjs
var import_react3 = __toESM(require_react(), 1);
var $9f79659886946c16$export$e5c5a5f917a5871c = Boolean(globalThis === null || globalThis === void 0 ? void 0 : globalThis.document) ? import_react3.useLayoutEffect : () => {
};

// node_modules/@radix-ui/react-form/node_modules/@radix-ui/react-id/dist/index.mjs
var $1746a345f3d73bb7$var$useReactId = $2AODx$react["useId".toString()] || (() => void 0);
var $1746a345f3d73bb7$var$count = 0;
function $1746a345f3d73bb7$export$f680877a34711e37(deterministicId) {
  const [id, setId] = $2AODx$react.useState($1746a345f3d73bb7$var$useReactId());
  $9f79659886946c16$export$e5c5a5f917a5871c(() => {
    if (!deterministicId) setId(
      (reactId) => reactId !== null && reactId !== void 0 ? reactId : String($1746a345f3d73bb7$var$count++)
    );
  }, [
    deterministicId
  ]);
  return deterministicId || (id ? `radix-${id}` : "");
}

// node_modules/@radix-ui/react-form/node_modules/@radix-ui/react-label/dist/index.mjs
var import_react6 = __toESM(require_react(), 1);

// node_modules/@radix-ui/react-form/node_modules/@radix-ui/react-primitive/dist/index.mjs
var import_react5 = __toESM(require_react(), 1);
var import_react_dom = __toESM(require_react_dom(), 1);

// node_modules/@radix-ui/react-form/node_modules/@radix-ui/react-slot/dist/index.mjs
var import_react4 = __toESM(require_react(), 1);
var $5e63c961fc1ce211$export$8c6ed5c666ac1360 = (0, import_react4.forwardRef)((props, forwardedRef) => {
  const { children, ...slotProps } = props;
  const childrenArray = import_react4.Children.toArray(children);
  const slottable = childrenArray.find($5e63c961fc1ce211$var$isSlottable);
  if (slottable) {
    const newElement = slottable.props.children;
    const newChildren = childrenArray.map((child) => {
      if (child === slottable) {
        if (import_react4.Children.count(newElement) > 1) return import_react4.Children.only(null);
        return (0, import_react4.isValidElement)(newElement) ? newElement.props.children : null;
      } else return child;
    });
    return (0, import_react4.createElement)($5e63c961fc1ce211$var$SlotClone, _extends({}, slotProps, {
      ref: forwardedRef
    }), (0, import_react4.isValidElement)(newElement) ? (0, import_react4.cloneElement)(newElement, void 0, newChildren) : null);
  }
  return (0, import_react4.createElement)($5e63c961fc1ce211$var$SlotClone, _extends({}, slotProps, {
    ref: forwardedRef
  }), children);
});
$5e63c961fc1ce211$export$8c6ed5c666ac1360.displayName = "Slot";
var $5e63c961fc1ce211$var$SlotClone = (0, import_react4.forwardRef)((props, forwardedRef) => {
  const { children, ...slotProps } = props;
  if ((0, import_react4.isValidElement)(children)) return (0, import_react4.cloneElement)(children, {
    ...$5e63c961fc1ce211$var$mergeProps(slotProps, children.props),
    ref: forwardedRef ? $6ed0406888f73fc4$export$43e446d32b3d21af(forwardedRef, children.ref) : children.ref
  });
  return import_react4.Children.count(children) > 1 ? import_react4.Children.only(null) : null;
});
$5e63c961fc1ce211$var$SlotClone.displayName = "SlotClone";
var $5e63c961fc1ce211$export$d9f1ccf0bdb05d45 = ({ children }) => {
  return (0, import_react4.createElement)(import_react4.Fragment, null, children);
};
function $5e63c961fc1ce211$var$isSlottable(child) {
  return (0, import_react4.isValidElement)(child) && child.type === $5e63c961fc1ce211$export$d9f1ccf0bdb05d45;
}
function $5e63c961fc1ce211$var$mergeProps(slotProps, childProps) {
  const overrideProps = {
    ...childProps
  };
  for (const propName in childProps) {
    const slotPropValue = slotProps[propName];
    const childPropValue = childProps[propName];
    const isHandler = /^on[A-Z]/.test(propName);
    if (isHandler) {
      if (slotPropValue && childPropValue) overrideProps[propName] = (...args) => {
        childPropValue(...args);
        slotPropValue(...args);
      };
      else if (slotPropValue) overrideProps[propName] = slotPropValue;
    } else if (propName === "style") overrideProps[propName] = {
      ...slotPropValue,
      ...childPropValue
    };
    else if (propName === "className") overrideProps[propName] = [
      slotPropValue,
      childPropValue
    ].filter(Boolean).join(" ");
  }
  return {
    ...slotProps,
    ...overrideProps
  };
}

// node_modules/@radix-ui/react-form/node_modules/@radix-ui/react-primitive/dist/index.mjs
var $8927f6f2acc4f386$var$NODES = [
  "a",
  "button",
  "div",
  "form",
  "h2",
  "h3",
  "img",
  "input",
  "label",
  "li",
  "nav",
  "ol",
  "p",
  "span",
  "svg",
  "ul"
];
var $8927f6f2acc4f386$export$250ffa63cdc0d034 = $8927f6f2acc4f386$var$NODES.reduce((primitive, node) => {
  const Node = (0, import_react5.forwardRef)((props, forwardedRef) => {
    const { asChild, ...primitiveProps } = props;
    const Comp = asChild ? $5e63c961fc1ce211$export$8c6ed5c666ac1360 : node;
    (0, import_react5.useEffect)(() => {
      window[Symbol.for("radix-ui")] = true;
    }, []);
    return (0, import_react5.createElement)(Comp, _extends({}, primitiveProps, {
      ref: forwardedRef
    }));
  });
  Node.displayName = `Primitive.${node}`;
  return {
    ...primitive,
    [node]: Node
  };
}, {});

// node_modules/@radix-ui/react-form/node_modules/@radix-ui/react-label/dist/index.mjs
var $b73a6c6685e72184$var$NAME = "Label";
var $b73a6c6685e72184$export$b04be29aa201d4f5 = (0, import_react6.forwardRef)((props, forwardedRef) => {
  return (0, import_react6.createElement)($8927f6f2acc4f386$export$250ffa63cdc0d034.label, _extends({}, props, {
    ref: forwardedRef,
    onMouseDown: (event) => {
      var _props$onMouseDown;
      (_props$onMouseDown = props.onMouseDown) === null || _props$onMouseDown === void 0 || _props$onMouseDown.call(props, event);
      if (!event.defaultPrevented && event.detail > 1) event.preventDefault();
    }
  }));
});
Object.assign($b73a6c6685e72184$export$b04be29aa201d4f5, {
  displayName: $b73a6c6685e72184$var$NAME
});

// node_modules/@radix-ui/react-form/dist/index.mjs
var [$d94698215c4408a7$var$createFormContext, $d94698215c4408a7$export$299997c7551e97cb] = $c512c27ab02ef895$export$50c7b4e9d9f19c1("Form");
var $d94698215c4408a7$var$FORM_NAME = "Form";
var [$d94698215c4408a7$var$ValidationProvider, $d94698215c4408a7$var$useValidationContext] = $d94698215c4408a7$var$createFormContext($d94698215c4408a7$var$FORM_NAME);
var [$d94698215c4408a7$var$AriaDescriptionProvider, $d94698215c4408a7$var$useAriaDescriptionContext] = $d94698215c4408a7$var$createFormContext($d94698215c4408a7$var$FORM_NAME);
var $d94698215c4408a7$export$a7fed597f4b8afd8 = (0, import_react7.forwardRef)((props, forwardedRef) => {
  const { __scopeForm, onClearServerErrors = () => {
  }, ...rootProps } = props;
  const formRef = (0, import_react7.useRef)(null);
  const composedFormRef = $6ed0406888f73fc4$export$c7b2cbe3552a0d05(forwardedRef, formRef);
  const [validityMap, setValidityMap] = (0, import_react7.useState)({});
  const getFieldValidity = (0, import_react7.useCallback)(
    (fieldName) => validityMap[fieldName],
    [
      validityMap
    ]
  );
  const handleFieldValidityChange = (0, import_react7.useCallback)(
    (fieldName, validity) => setValidityMap((prevValidityMap) => {
      var _prevValidityMap$fiel;
      return {
        ...prevValidityMap,
        [fieldName]: {
          ...(_prevValidityMap$fiel = prevValidityMap[fieldName]) !== null && _prevValidityMap$fiel !== void 0 ? _prevValidityMap$fiel : {},
          ...validity
        }
      };
    }),
    []
  );
  const handleFieldValiditionClear = (0, import_react7.useCallback)((fieldName) => {
    setValidityMap(
      (prevValidityMap) => ({
        ...prevValidityMap,
        [fieldName]: void 0
      })
    );
    setCustomErrorsMap(
      (prevCustomErrorsMap) => ({
        ...prevCustomErrorsMap,
        [fieldName]: {}
      })
    );
  }, []);
  const [customMatcherEntriesMap, setCustomMatcherEntriesMap] = (0, import_react7.useState)({});
  const getFieldCustomMatcherEntries = (0, import_react7.useCallback)((fieldName) => {
    var _customMatcherEntries;
    return (_customMatcherEntries = customMatcherEntriesMap[fieldName]) !== null && _customMatcherEntries !== void 0 ? _customMatcherEntries : [];
  }, [
    customMatcherEntriesMap
  ]);
  const handleFieldCustomMatcherAdd = (0, import_react7.useCallback)((fieldName, matcherEntry) => {
    setCustomMatcherEntriesMap((prevCustomMatcherEntriesMap) => {
      var _prevCustomMatcherEnt;
      return {
        ...prevCustomMatcherEntriesMap,
        [fieldName]: [
          ...(_prevCustomMatcherEnt = prevCustomMatcherEntriesMap[fieldName]) !== null && _prevCustomMatcherEnt !== void 0 ? _prevCustomMatcherEnt : [],
          matcherEntry
        ]
      };
    });
  }, []);
  const handleFieldCustomMatcherRemove = (0, import_react7.useCallback)((fieldName, matcherEntryId) => {
    setCustomMatcherEntriesMap((prevCustomMatcherEntriesMap) => {
      var _prevCustomMatcherEnt2;
      return {
        ...prevCustomMatcherEntriesMap,
        [fieldName]: ((_prevCustomMatcherEnt2 = prevCustomMatcherEntriesMap[fieldName]) !== null && _prevCustomMatcherEnt2 !== void 0 ? _prevCustomMatcherEnt2 : []).filter(
          (matcherEntry) => matcherEntry.id !== matcherEntryId
        )
      };
    });
  }, []);
  const [customErrorsMap, setCustomErrorsMap] = (0, import_react7.useState)({});
  const getFieldCustomErrors = (0, import_react7.useCallback)((fieldName) => {
    var _customErrorsMap$fiel;
    return (_customErrorsMap$fiel = customErrorsMap[fieldName]) !== null && _customErrorsMap$fiel !== void 0 ? _customErrorsMap$fiel : {};
  }, [
    customErrorsMap
  ]);
  const handleFieldCustomErrorsChange = (0, import_react7.useCallback)((fieldName, customErrors) => {
    setCustomErrorsMap((prevCustomErrorsMap) => {
      var _prevCustomErrorsMap$;
      return {
        ...prevCustomErrorsMap,
        [fieldName]: {
          ...(_prevCustomErrorsMap$ = prevCustomErrorsMap[fieldName]) !== null && _prevCustomErrorsMap$ !== void 0 ? _prevCustomErrorsMap$ : {},
          ...customErrors
        }
      };
    });
  }, []);
  const [messageIdsMap, setMessageIdsMap] = (0, import_react7.useState)({});
  const handleFieldMessageIdAdd = (0, import_react7.useCallback)((fieldName, id) => {
    setMessageIdsMap((prevMessageIdsMap) => {
      const fieldDescriptionIds = new Set(prevMessageIdsMap[fieldName]).add(id);
      return {
        ...prevMessageIdsMap,
        [fieldName]: fieldDescriptionIds
      };
    });
  }, []);
  const handleFieldMessageIdRemove = (0, import_react7.useCallback)((fieldName, id) => {
    setMessageIdsMap((prevMessageIdsMap) => {
      const fieldDescriptionIds = new Set(prevMessageIdsMap[fieldName]);
      fieldDescriptionIds.delete(id);
      return {
        ...prevMessageIdsMap,
        [fieldName]: fieldDescriptionIds
      };
    });
  }, []);
  const getFieldDescription = (0, import_react7.useCallback)((fieldName) => {
    var _messageIdsMap$fieldN;
    return Array.from((_messageIdsMap$fieldN = messageIdsMap[fieldName]) !== null && _messageIdsMap$fieldN !== void 0 ? _messageIdsMap$fieldN : []).join(" ") || void 0;
  }, [
    messageIdsMap
  ]);
  return (0, import_react7.createElement)($d94698215c4408a7$var$ValidationProvider, {
    scope: __scopeForm,
    getFieldValidity,
    onFieldValidityChange: handleFieldValidityChange,
    getFieldCustomMatcherEntries,
    onFieldCustomMatcherEntryAdd: handleFieldCustomMatcherAdd,
    onFieldCustomMatcherEntryRemove: handleFieldCustomMatcherRemove,
    getFieldCustomErrors,
    onFieldCustomErrorsChange: handleFieldCustomErrorsChange,
    onFieldValiditionClear: handleFieldValiditionClear
  }, (0, import_react7.createElement)($d94698215c4408a7$var$AriaDescriptionProvider, {
    scope: __scopeForm,
    onFieldMessageIdAdd: handleFieldMessageIdAdd,
    onFieldMessageIdRemove: handleFieldMessageIdRemove,
    getFieldDescription
  }, (0, import_react7.createElement)($8927f6f2acc4f386$export$250ffa63cdc0d034.form, _extends({}, rootProps, {
    ref: composedFormRef,
    onInvalid: $e42e1063c40fb3ef$export$b9ecd428b558ff10(props.onInvalid, (event) => {
      const firstInvalidControl = $d94698215c4408a7$var$getFirstInvalidControl(event.currentTarget);
      if (firstInvalidControl === event.target) firstInvalidControl.focus();
      event.preventDefault();
    }),
    onSubmit: $e42e1063c40fb3ef$export$b9ecd428b558ff10(props.onSubmit, onClearServerErrors, {
      checkForDefaultPrevented: false
    }),
    onReset: $e42e1063c40fb3ef$export$b9ecd428b558ff10(props.onReset, onClearServerErrors)
  }))));
});
Object.assign($d94698215c4408a7$export$a7fed597f4b8afd8, {
  displayName: $d94698215c4408a7$var$FORM_NAME
});
var $d94698215c4408a7$var$FIELD_NAME = "FormField";
var [$d94698215c4408a7$var$FormFieldProvider, $d94698215c4408a7$var$useFormFieldContext] = $d94698215c4408a7$var$createFormContext($d94698215c4408a7$var$FIELD_NAME);
var $d94698215c4408a7$export$56e87bf42978147a = (0, import_react7.forwardRef)((props, forwardedRef) => {
  const { __scopeForm, name, serverInvalid = false, ...fieldProps } = props;
  const validationContext = $d94698215c4408a7$var$useValidationContext($d94698215c4408a7$var$FIELD_NAME, __scopeForm);
  const validity = validationContext.getFieldValidity(name);
  const id = $1746a345f3d73bb7$export$f680877a34711e37();
  return (0, import_react7.createElement)($d94698215c4408a7$var$FormFieldProvider, {
    scope: __scopeForm,
    id,
    name,
    serverInvalid
  }, (0, import_react7.createElement)($8927f6f2acc4f386$export$250ffa63cdc0d034.div, _extends({
    "data-valid": $d94698215c4408a7$var$getValidAttribute(validity, serverInvalid),
    "data-invalid": $d94698215c4408a7$var$getInvalidAttribute(validity, serverInvalid)
  }, fieldProps, {
    ref: forwardedRef
  })));
});
Object.assign($d94698215c4408a7$export$56e87bf42978147a, {
  displayName: $d94698215c4408a7$var$FIELD_NAME
});
var $d94698215c4408a7$var$LABEL_NAME = "FormLabel";
var $d94698215c4408a7$export$842aba50ed0ce9d7 = (0, import_react7.forwardRef)((props, forwardedRef) => {
  const { __scopeForm, ...labelProps } = props;
  const validationContext = $d94698215c4408a7$var$useValidationContext($d94698215c4408a7$var$LABEL_NAME, __scopeForm);
  const fieldContext = $d94698215c4408a7$var$useFormFieldContext($d94698215c4408a7$var$LABEL_NAME, __scopeForm);
  const htmlFor = labelProps.htmlFor || fieldContext.id;
  const validity = validationContext.getFieldValidity(fieldContext.name);
  return (0, import_react7.createElement)($b73a6c6685e72184$export$b04be29aa201d4f5, _extends({
    "data-valid": $d94698215c4408a7$var$getValidAttribute(validity, fieldContext.serverInvalid),
    "data-invalid": $d94698215c4408a7$var$getInvalidAttribute(validity, fieldContext.serverInvalid)
  }, labelProps, {
    ref: forwardedRef,
    htmlFor
  }));
});
Object.assign($d94698215c4408a7$export$842aba50ed0ce9d7, {
  displayName: $d94698215c4408a7$var$LABEL_NAME
});
var $d94698215c4408a7$var$CONTROL_NAME = "FormControl";
var $d94698215c4408a7$export$fe5d99d8691b3f62 = (0, import_react7.forwardRef)((props, forwardedRef) => {
  const { __scopeForm, ...controlProps } = props;
  const validationContext = $d94698215c4408a7$var$useValidationContext($d94698215c4408a7$var$CONTROL_NAME, __scopeForm);
  const fieldContext = $d94698215c4408a7$var$useFormFieldContext($d94698215c4408a7$var$CONTROL_NAME, __scopeForm);
  const ariaDescriptionContext = $d94698215c4408a7$var$useAriaDescriptionContext($d94698215c4408a7$var$CONTROL_NAME, __scopeForm);
  const ref = (0, import_react7.useRef)(null);
  const composedRef = $6ed0406888f73fc4$export$c7b2cbe3552a0d05(forwardedRef, ref);
  const name = controlProps.name || fieldContext.name;
  const id1 = controlProps.id || fieldContext.id;
  const customMatcherEntries = validationContext.getFieldCustomMatcherEntries(name);
  const { onFieldValidityChange, onFieldCustomErrorsChange, onFieldValiditionClear } = validationContext;
  const updateControlValidity = (0, import_react7.useCallback)(async (control) => {
    if ($d94698215c4408a7$var$hasBuiltInError(control.validity)) {
      const controlValidity2 = $d94698215c4408a7$var$validityStateToObject(control.validity);
      onFieldValidityChange(name, controlValidity2);
      return;
    }
    const formData = control.form ? new FormData(control.form) : new FormData();
    const matcherArgs = [
      control.value,
      formData
    ];
    const syncCustomMatcherEntries = [];
    const ayncCustomMatcherEntries = [];
    customMatcherEntries.forEach((customMatcherEntry) => {
      if ($d94698215c4408a7$var$isAsyncCustomMatcherEntry(customMatcherEntry, matcherArgs)) ayncCustomMatcherEntries.push(customMatcherEntry);
      else if ($d94698215c4408a7$var$isSyncCustomMatcherEntry(customMatcherEntry)) syncCustomMatcherEntries.push(customMatcherEntry);
    });
    const syncCustomErrors = syncCustomMatcherEntries.map(({ id, match }) => {
      return [
        id,
        match(...matcherArgs)
      ];
    });
    const syncCustomErrorsById = Object.fromEntries(syncCustomErrors);
    const hasSyncCustomErrors = Object.values(syncCustomErrorsById).some(Boolean);
    const hasCustomError = hasSyncCustomErrors;
    control.setCustomValidity(hasCustomError ? $d94698215c4408a7$var$DEFAULT_INVALID_MESSAGE : "");
    const controlValidity = $d94698215c4408a7$var$validityStateToObject(control.validity);
    onFieldValidityChange(name, controlValidity);
    onFieldCustomErrorsChange(name, syncCustomErrorsById);
    if (!hasSyncCustomErrors && ayncCustomMatcherEntries.length > 0) {
      const promisedCustomErrors = ayncCustomMatcherEntries.map(
        ({ id, match }) => match(...matcherArgs).then(
          (matches) => [
            id,
            matches
          ]
        )
      );
      const asyncCustomErrors = await Promise.all(promisedCustomErrors);
      const asyncCustomErrorsById = Object.fromEntries(asyncCustomErrors);
      const hasAsyncCustomErrors = Object.values(asyncCustomErrorsById).some(Boolean);
      const hasCustomError2 = hasAsyncCustomErrors;
      control.setCustomValidity(hasCustomError2 ? $d94698215c4408a7$var$DEFAULT_INVALID_MESSAGE : "");
      const controlValidity2 = $d94698215c4408a7$var$validityStateToObject(control.validity);
      onFieldValidityChange(name, controlValidity2);
      onFieldCustomErrorsChange(name, asyncCustomErrorsById);
    }
  }, [
    customMatcherEntries,
    name,
    onFieldCustomErrorsChange,
    onFieldValidityChange
  ]);
  (0, import_react7.useEffect)(() => {
    const control = ref.current;
    if (control) {
      const handleChange = () => updateControlValidity(control);
      control.addEventListener("change", handleChange);
      return () => control.removeEventListener("change", handleChange);
    }
  }, [
    updateControlValidity
  ]);
  const resetControlValidity = (0, import_react7.useCallback)(() => {
    const control = ref.current;
    if (control) {
      control.setCustomValidity("");
      onFieldValiditionClear(name);
    }
  }, [
    name,
    onFieldValiditionClear
  ]);
  (0, import_react7.useEffect)(() => {
    var _ref$current;
    const form = (_ref$current = ref.current) === null || _ref$current === void 0 ? void 0 : _ref$current.form;
    if (form) {
      form.addEventListener("reset", resetControlValidity);
      return () => form.removeEventListener("reset", resetControlValidity);
    }
  }, [
    resetControlValidity
  ]);
  (0, import_react7.useEffect)(() => {
    const control = ref.current;
    const form = control === null || control === void 0 ? void 0 : control.closest("form");
    if (form && fieldContext.serverInvalid) {
      const firstInvalidControl = $d94698215c4408a7$var$getFirstInvalidControl(form);
      if (firstInvalidControl === control) firstInvalidControl.focus();
    }
  }, [
    fieldContext.serverInvalid
  ]);
  const validity = validationContext.getFieldValidity(name);
  return (0, import_react7.createElement)($8927f6f2acc4f386$export$250ffa63cdc0d034.input, _extends({
    "data-valid": $d94698215c4408a7$var$getValidAttribute(validity, fieldContext.serverInvalid),
    "data-invalid": $d94698215c4408a7$var$getInvalidAttribute(validity, fieldContext.serverInvalid),
    "aria-invalid": fieldContext.serverInvalid ? true : void 0,
    "aria-describedby": ariaDescriptionContext.getFieldDescription(name),
    title: ""
  }, controlProps, {
    ref: composedRef,
    id: id1,
    name,
    onInvalid: $e42e1063c40fb3ef$export$b9ecd428b558ff10(props.onInvalid, (event) => {
      const control = event.currentTarget;
      updateControlValidity(control);
    }),
    onChange: $e42e1063c40fb3ef$export$b9ecd428b558ff10(props.onChange, (event) => {
      resetControlValidity();
    })
  }));
});
Object.assign($d94698215c4408a7$export$fe5d99d8691b3f62, {
  displayName: $d94698215c4408a7$var$CONTROL_NAME
});
var $d94698215c4408a7$var$DEFAULT_INVALID_MESSAGE = "This value is not valid";
var $d94698215c4408a7$var$DEFAULT_BUILT_IN_MESSAGES = {
  badInput: $d94698215c4408a7$var$DEFAULT_INVALID_MESSAGE,
  patternMismatch: "This value does not match the required pattern",
  rangeOverflow: "This value is too large",
  rangeUnderflow: "This value is too small",
  stepMismatch: "This value does not match the required step",
  tooLong: "This value is too long",
  tooShort: "This value is too short",
  typeMismatch: "This value does not match the required type",
  valid: void 0,
  valueMissing: "This value is missing"
};
var $d94698215c4408a7$var$MESSAGE_NAME = "FormMessage";
var $d94698215c4408a7$export$2e8ae7a1a126169a = (0, import_react7.forwardRef)((props, forwardedRef) => {
  const { match, name: nameProp, ...messageProps } = props;
  const fieldContext = $d94698215c4408a7$var$useFormFieldContext($d94698215c4408a7$var$MESSAGE_NAME, props.__scopeForm);
  const name = nameProp !== null && nameProp !== void 0 ? nameProp : fieldContext.name;
  if (match === void 0) return (0, import_react7.createElement)($d94698215c4408a7$var$FormMessageImpl, _extends({}, messageProps, {
    ref: forwardedRef,
    name
  }), props.children || $d94698215c4408a7$var$DEFAULT_INVALID_MESSAGE);
  else if (typeof match === "function") return (0, import_react7.createElement)($d94698215c4408a7$var$FormCustomMessage, _extends({
    match
  }, messageProps, {
    ref: forwardedRef,
    name
  }));
  else return (0, import_react7.createElement)($d94698215c4408a7$var$FormBuiltInMessage, _extends({
    match
  }, messageProps, {
    ref: forwardedRef,
    name
  }));
});
Object.assign($d94698215c4408a7$export$2e8ae7a1a126169a, {
  displayName: $d94698215c4408a7$var$MESSAGE_NAME
});
var $d94698215c4408a7$var$FormBuiltInMessage = (0, import_react7.forwardRef)((props, forwardedRef) => {
  const { match, forceMatch = false, name, children, ...messageProps } = props;
  const validationContext = $d94698215c4408a7$var$useValidationContext($d94698215c4408a7$var$MESSAGE_NAME, messageProps.__scopeForm);
  const validity = validationContext.getFieldValidity(name);
  const matches = forceMatch || (validity === null || validity === void 0 ? void 0 : validity[match]);
  if (matches) return (0, import_react7.createElement)($d94698215c4408a7$var$FormMessageImpl, _extends({
    ref: forwardedRef
  }, messageProps, {
    name
  }), children !== null && children !== void 0 ? children : $d94698215c4408a7$var$DEFAULT_BUILT_IN_MESSAGES[match]);
  return null;
});
var $d94698215c4408a7$var$FormCustomMessage = (0, import_react7.forwardRef)((props, forwardedRef) => {
  const { match, forceMatch = false, name, id: idProp, children, ...messageProps } = props;
  const validationContext = $d94698215c4408a7$var$useValidationContext($d94698215c4408a7$var$MESSAGE_NAME, messageProps.__scopeForm);
  const ref = (0, import_react7.useRef)(null);
  const composedRef = $6ed0406888f73fc4$export$c7b2cbe3552a0d05(forwardedRef, ref);
  const _id = $1746a345f3d73bb7$export$f680877a34711e37();
  const id = idProp !== null && idProp !== void 0 ? idProp : _id;
  const customMatcherEntry = (0, import_react7.useMemo)(
    () => ({
      id,
      match
    }),
    [
      id,
      match
    ]
  );
  const { onFieldCustomMatcherEntryAdd, onFieldCustomMatcherEntryRemove } = validationContext;
  (0, import_react7.useEffect)(() => {
    onFieldCustomMatcherEntryAdd(name, customMatcherEntry);
    return () => onFieldCustomMatcherEntryRemove(name, customMatcherEntry.id);
  }, [
    customMatcherEntry,
    name,
    onFieldCustomMatcherEntryAdd,
    onFieldCustomMatcherEntryRemove
  ]);
  const validity = validationContext.getFieldValidity(name);
  const customErrors = validationContext.getFieldCustomErrors(name);
  const hasMatchingCustomError = customErrors[id];
  const matches = forceMatch || validity && !$d94698215c4408a7$var$hasBuiltInError(validity) && hasMatchingCustomError;
  if (matches) return (0, import_react7.createElement)($d94698215c4408a7$var$FormMessageImpl, _extends({
    id,
    ref: composedRef
  }, messageProps, {
    name
  }), children !== null && children !== void 0 ? children : $d94698215c4408a7$var$DEFAULT_INVALID_MESSAGE);
  return null;
});
var $d94698215c4408a7$var$FormMessageImpl = (0, import_react7.forwardRef)((props, forwardedRef) => {
  const { __scopeForm, id: idProp, name, ...messageProps } = props;
  const ariaDescriptionContext = $d94698215c4408a7$var$useAriaDescriptionContext($d94698215c4408a7$var$MESSAGE_NAME, __scopeForm);
  const _id = $1746a345f3d73bb7$export$f680877a34711e37();
  const id = idProp !== null && idProp !== void 0 ? idProp : _id;
  const { onFieldMessageIdAdd, onFieldMessageIdRemove } = ariaDescriptionContext;
  (0, import_react7.useEffect)(() => {
    onFieldMessageIdAdd(name, id);
    return () => onFieldMessageIdRemove(name, id);
  }, [
    name,
    id,
    onFieldMessageIdAdd,
    onFieldMessageIdRemove
  ]);
  return (0, import_react7.createElement)($8927f6f2acc4f386$export$250ffa63cdc0d034.span, _extends({
    id
  }, messageProps, {
    ref: forwardedRef
  }));
});
var $d94698215c4408a7$var$VALIDITY_STATE_NAME = "FormValidityState";
var $d94698215c4408a7$export$7a93102810e06862 = (props) => {
  const { __scopeForm, name: nameProp, children } = props;
  const validationContext = $d94698215c4408a7$var$useValidationContext($d94698215c4408a7$var$VALIDITY_STATE_NAME, __scopeForm);
  const fieldContext = $d94698215c4408a7$var$useFormFieldContext($d94698215c4408a7$var$VALIDITY_STATE_NAME, __scopeForm);
  const name = nameProp !== null && nameProp !== void 0 ? nameProp : fieldContext.name;
  const validity = validationContext.getFieldValidity(name);
  return (0, import_react7.createElement)(import_react7.Fragment, null, children(validity));
};
Object.assign($d94698215c4408a7$export$7a93102810e06862, {
  displayName: $d94698215c4408a7$var$VALIDITY_STATE_NAME
});
var $d94698215c4408a7$var$SUBMIT_NAME = "FormSubmit";
var $d94698215c4408a7$export$d0861e5bd09bd9e4 = (0, import_react7.forwardRef)((props, forwardedRef) => {
  const { __scopeForm, ...submitProps } = props;
  return (0, import_react7.createElement)($8927f6f2acc4f386$export$250ffa63cdc0d034.button, _extends({
    type: "submit"
  }, submitProps, {
    ref: forwardedRef
  }));
});
Object.assign($d94698215c4408a7$export$d0861e5bd09bd9e4, {
  displayName: $d94698215c4408a7$var$SUBMIT_NAME
});
function $d94698215c4408a7$var$validityStateToObject(validity) {
  const object = {};
  for (const key in validity) object[key] = validity[key];
  return object;
}
function $d94698215c4408a7$var$isHTMLElement(element) {
  return element instanceof HTMLElement;
}
function $d94698215c4408a7$var$isFormControl(element) {
  return "validity" in element;
}
function $d94698215c4408a7$var$isInvalid(control) {
  return $d94698215c4408a7$var$isFormControl(control) && (control.validity.valid === false || control.getAttribute("aria-invalid") === "true");
}
function $d94698215c4408a7$var$getFirstInvalidControl(form) {
  const elements = form.elements;
  const [firstInvalidControl] = Array.from(elements).filter($d94698215c4408a7$var$isHTMLElement).filter($d94698215c4408a7$var$isInvalid);
  return firstInvalidControl;
}
function $d94698215c4408a7$var$isAsyncCustomMatcherEntry(entry, args) {
  return entry.match.constructor.name === "AsyncFunction" || $d94698215c4408a7$var$returnsPromise(entry.match, args);
}
function $d94698215c4408a7$var$isSyncCustomMatcherEntry(entry) {
  return entry.match.constructor.name === "Function";
}
function $d94698215c4408a7$var$returnsPromise(func, args) {
  return func(...args) instanceof Promise;
}
function $d94698215c4408a7$var$hasBuiltInError(validity) {
  let error = false;
  for (const validityKey in validity) {
    const key = validityKey;
    if (key !== "valid" && key !== "customError" && validity[key]) {
      error = true;
      break;
    }
  }
  return error;
}
function $d94698215c4408a7$var$getValidAttribute(validity, serverInvalid) {
  if ((validity === null || validity === void 0 ? void 0 : validity.valid) === true && !serverInvalid) return true;
  return void 0;
}
function $d94698215c4408a7$var$getInvalidAttribute(validity, serverInvalid) {
  if ((validity === null || validity === void 0 ? void 0 : validity.valid) === false || serverInvalid) return true;
  return void 0;
}
var $d94698215c4408a7$export$be92b6f5f03c0fe9 = $d94698215c4408a7$export$a7fed597f4b8afd8;
var $d94698215c4408a7$export$a455218a85c89869 = $d94698215c4408a7$export$56e87bf42978147a;
var $d94698215c4408a7$export$b04be29aa201d4f5 = $d94698215c4408a7$export$842aba50ed0ce9d7;
var $d94698215c4408a7$export$7a7fa4424cb20976 = $d94698215c4408a7$export$fe5d99d8691b3f62;
var $d94698215c4408a7$export$f69c19e57285b83a = $d94698215c4408a7$export$2e8ae7a1a126169a;
var $d94698215c4408a7$export$5efdf844224572d9 = $d94698215c4408a7$export$7a93102810e06862;
var $d94698215c4408a7$export$2c4cf1f7b42ef78c = $d94698215c4408a7$export$d0861e5bd09bd9e4;
export {
  $d94698215c4408a7$export$7a7fa4424cb20976 as Control,
  $d94698215c4408a7$export$a455218a85c89869 as Field,
  $d94698215c4408a7$export$a7fed597f4b8afd8 as Form,
  $d94698215c4408a7$export$fe5d99d8691b3f62 as FormControl,
  $d94698215c4408a7$export$56e87bf42978147a as FormField,
  $d94698215c4408a7$export$842aba50ed0ce9d7 as FormLabel,
  $d94698215c4408a7$export$2e8ae7a1a126169a as FormMessage,
  $d94698215c4408a7$export$d0861e5bd09bd9e4 as FormSubmit,
  $d94698215c4408a7$export$7a93102810e06862 as FormValidityState,
  $d94698215c4408a7$export$b04be29aa201d4f5 as Label,
  $d94698215c4408a7$export$f69c19e57285b83a as Message,
  $d94698215c4408a7$export$be92b6f5f03c0fe9 as Root,
  $d94698215c4408a7$export$2c4cf1f7b42ef78c as Submit,
  $d94698215c4408a7$export$5efdf844224572d9 as ValidityState,
  $d94698215c4408a7$export$299997c7551e97cb as createFormScope
};
//# sourceMappingURL=@radix-ui_react-form.js.map
