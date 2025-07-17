import * as yup from 'yup';

export const forgotPasswordSchema = yup.object().shape({
  email: yup
    .string()
    .email('Por favor ingresa un correo electrónico válido')
    .required('El correo electrónico es requerido'),
});

export const resetPasswordSchema = yup.object().shape({
  newPassword: yup
    .string()
    .min(8, 'La contraseña debe tener al menos 8 caracteres')
    .required('La nueva contraseña es requerida'),
  confirmPassword: yup
    .string()
    .oneOf([yup.ref('newPassword')], 'Las contraseñas deben coincidir')
    .required('Por favor confirma tu contraseña'),
});

export type ForgotPasswordFormData = yup.InferType<typeof forgotPasswordSchema>;
export type ResetPasswordFormData = yup.InferType<typeof resetPasswordSchema>;
