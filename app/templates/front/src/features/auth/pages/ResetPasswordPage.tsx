import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { yupResolver } from '@hookform/resolvers/yup';
import { Lock, CheckCircle2 } from 'lucide-react';
import { Link, useParams, useNavigate } from 'react-router-dom';
import { resetPasswordSchema, ResetPasswordFormData } from '../schemas/password-reset.schema';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Icons } from '@/components/icons';

type ResetPasswordParams = {
  uid: string;
  token: string;
};

export function ResetPasswordPage() {
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { uid, token } = useParams<keyof ResetPasswordParams>() as ResetPasswordParams;
  const navigate = useNavigate();

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ResetPasswordFormData>({
    resolver: yupResolver(resetPasswordSchema),
  });

  const onSubmit = async (data: ResetPasswordFormData) => {
    setIsLoading(true);
    setError(null);

    try {
      // Simular llamada a la API
      // await api.post(`/auth/password/reset/confirm/${uid}/${token}/`, {
      //   new_password: data.newPassword,
      //   re_new_password: data.confirmPassword,
      //   uid,
      //   token,
      // });
      
      await new Promise(resolve => setTimeout(resolve, 1500)); // Simular delay
      setIsSubmitted(true);
      
      // Redirigir al login después de 3 segundos
      setTimeout(() => {
        navigate('/login', { 
          state: { 
            message: 'Tu contraseña ha sido restablecida exitosamente. Por favor inicia sesión.' 
          } 
        });
      }, 3000);
    } catch (err) {
      console.error('Error al restablecer contraseña:', err);
      setError(
        'El enlace de restablecimiento es inválido o ha expirado. Por favor, solicita uno nuevo.'
      );
    } finally {
      setIsLoading(false);
    }
  };

  if (isSubmitted) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-gray-50 px-4">
        <div className="w-full max-w-md space-y-6">
          <div className="flex flex-col items-center">
            <Icons.logo className="h-12 w-auto text-blue-600" />
            <h1 className="mt-4 text-2xl font-bold text-gray-900">¡Contraseña actualizada!</h1>
          </div>

          <div className="bg-white p-8 rounded-lg shadow-sm border border-gray-200">
            <div className="text-center">
              <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-green-100">
                <CheckCircle2 className="h-6 w-6 text-green-600" />
              </div>
              <h2 className="mt-3 text-lg font-medium text-gray-900">Contraseña restablecida</h2>
              <p className="mt-2 text-sm text-gray-500">
                Tu contraseña ha sido actualizada exitosamente. Serás redirigido al inicio de sesión...
              </p>
              <div className="mt-6">
                <Link to="/login">
                  <Button variant="outline">
                    Ir al inicio de sesión
                  </Button>
                </Link>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gray-50 px-4">
      <div className="w-full max-w-md space-y-6">
        <div className="flex flex-col items-center">
          <Icons.logo className="h-12 w-auto text-blue-600" />
          <h1 className="mt-4 text-2xl font-bold text-gray-900">Restablecer contraseña</h1>
          <p className="mt-1 text-sm text-gray-500 text-center">
            Crea una nueva contraseña segura para tu cuenta.
          </p>
        </div>

        {error && (
          <div className="p-4 text-sm text-red-700 bg-red-100 rounded-lg">
            {error}
          </div>
        )}

        <div className="bg-white p-8 rounded-lg shadow-sm border border-gray-200">
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
            <div>
              <Label htmlFor="newPassword" className="block text-sm font-medium text-gray-700">
                Nueva contraseña
              </Label>
              <div className="mt-1 relative rounded-md shadow-sm">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Lock className="h-5 w-5 text-gray-400" />
                </div>
                <Input
                  id="newPassword"
                  type="password"
                  autoComplete="new-password"
                  className={`pl-10 ${errors.newPassword ? 'border-red-300' : ''}`}
                  {...register('newPassword')}
                  disabled={isLoading}
                />
              </div>
              {errors.newPassword && (
                <p className="mt-1 text-sm text-red-600">{errors.newPassword.message}</p>
              )}
              <p className="mt-1 text-xs text-gray-500">
                Mínimo 8 caracteres
              </p>
            </div>

            <div>
              <Label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700">
                Confirmar contraseña
              </Label>
              <div className="mt-1 relative rounded-md shadow-sm">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Lock className="h-5 w-5 text-gray-400" />
                </div>
                <Input
                  id="confirmPassword"
                  type="password"
                  autoComplete="new-password"
                  className={`pl-10 ${errors.confirmPassword ? 'border-red-300' : ''}`}
                  {...register('confirmPassword')}
                  disabled={isLoading}
                />
              </div>
              {errors.confirmPassword && (
                <p className="mt-1 text-sm text-red-600">{errors.confirmPassword.message}</p>
              )}
            </div>

            <div>
              <Button
                type="submit"
                className="w-full justify-center"
                disabled={isLoading}
              >
                {isLoading ? (
                  <>
                    <Icons.spinner className="mr-2 h-4 w-4 animate-spin" />
                    Actualizando...
                  </>
                ) : (
                  'Actualizar contraseña'
                )}
              </Button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
