import { useState, useCallback, useEffect } from 'react';
import Validator, { ValidationSchema, ValidationResult } from '../utils/validation';

interface UseFormValidationOptions {
  schema: ValidationSchema;
  initialValues?: Record<string, any>;
  validateOnChange?: boolean;
  validateOnBlur?: boolean;
}

interface FormState {
  values: Record<string, any>;
  errors: Record<string, string[]>;
  touched: Record<string, boolean>;
  isValid: boolean;
  isDirty: boolean;
}

interface FormActions {
  setValue: (field: string, value: any) => void;
  setValues: (values: Record<string, any>) => void;
  setError: (field: string, error: string) => void;
  setErrors: (errors: Record<string, string[]>) => void;
  setTouched: (field: string, touched: boolean) => void;
  validateField: (field: string) => void;
  validateForm: () => ValidationResult;
  reset: () => void;
  resetErrors: () => void;
}

export function useFormValidation({
  schema,
  initialValues = {},
  validateOnChange = true,
  validateOnBlur = true,
}: UseFormValidationOptions): [FormState, FormActions] {
  const [state, setState] = useState<FormState>({
    values: initialValues,
    errors: {},
    touched: {},
    isValid: false,
    isDirty: false,
  });

  // Validate a single field
  const validateField = useCallback((field: string) => {
    const rule = schema[field];
    if (!rule) return;

    const result = Validator.validateField(state.values[field], rule);
    
    setState(prev => ({
      ...prev,
      errors: {
        ...prev.errors,
        [field]: result.errors,
      },
    }));
  }, [schema, state.values]);

  // Validate entire form
  const validateForm = useCallback((): ValidationResult => {
    const result = Validator.validateObject(state.values, schema);
    
    setState(prev => ({
      ...prev,
      errors: Object.fromEntries(
        Object.keys(schema).map(field => [
          field,
          result.errors.filter(error => error.startsWith(`${field}:`))
            .map(error => error.replace(`${field}: `, ''))
        ])
      ),
      isValid: result.isValid,
    }));

    return result;
  }, [state.values, schema]);

  // Set a single field value
  const setValue = useCallback((field: string, value: any) => {
    setState(prev => {
      const newValues = { ...prev.values, [field]: value };
      const newErrors = { ...prev.errors };
      
      // Clear error for this field
      delete newErrors[field];
      
      const newState = {
        ...prev,
        values: newValues,
        errors: newErrors,
        isDirty: true,
      };

      // Validate on change if enabled
      if (validateOnChange && schema[field]) {
        const result = Validator.validateField(value, schema[field]);
        if (!result.isValid) {
          newState.errors[field] = result.errors;
        }
      }

      return newState;
    });
  }, [schema, validateOnChange]);

  // Set multiple field values
  const setValues = useCallback((values: Record<string, any>) => {
    setState(prev => ({
      ...prev,
      values: { ...prev.values, ...values },
      isDirty: true,
    }));
  }, []);

  // Set a single field error
  const setError = useCallback((field: string, error: string) => {
    setState(prev => ({
      ...prev,
      errors: { ...prev.errors, [field]: [error] },
    }));
  }, []);

  // Set multiple field errors
  const setErrors = useCallback((errors: Record<string, string[]>) => {
    setState(prev => ({
      ...prev,
      errors: { ...prev.errors, ...errors },
    }));
  }, []);

  // Set field touched state
  const setTouched = useCallback((field: string, touched: boolean) => {
    setState(prev => ({
      ...prev,
      touched: { ...prev.touched, [field]: touched },
    }));

    // Validate on blur if enabled
    if (validateOnBlur && touched && schema[field]) {
      validateField(field);
    }
  }, [schema, validateOnBlur, validateField]);

  // Reset form to initial state
  const reset = useCallback(() => {
    setState({
      values: initialValues,
      errors: {},
      touched: {},
      isValid: false,
      isDirty: false,
    });
  }, [initialValues]);

  // Reset only errors
  const resetErrors = useCallback(() => {
    setState(prev => ({
      ...prev,
      errors: {},
      isValid: false,
    }));
  }, []);

  // Validate form on mount and when schema changes
  useEffect(() => {
    validateForm();
  }, [validateForm]);

  const actions: FormActions = {
    setValue,
    setValues,
    setError,
    setErrors,
    setTouched,
    validateField,
    validateForm,
    reset,
    resetErrors,
  };

  return [state, actions];
}

// Convenience hook for simple field validation
export function useFieldValidation(
  value: any,
  rule: any,
  validateOnChange = true
): [string[], (newValue: any) => void] {
  const [errors, setErrors] = useState<string[]>([]);

  const validate = useCallback((newValue: any) => {
    if (validateOnChange) {
      const result = Validator.validateField(newValue, rule);
      setErrors(result.errors);
    }
  }, [rule, validateOnChange]);

  useEffect(() => {
    validate(value);
  }, [value, validate]);

  return [errors, validate];
}

export default useFormValidation;
