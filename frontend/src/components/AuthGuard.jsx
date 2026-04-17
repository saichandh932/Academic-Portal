import { Navigate, useLocation } from 'react-router-dom';

/**
 * ProtectedRoute component
 * Checks if the user has a valid role and ID in sessionStorage.
 * If not, redirects to the login page.
 */
export function ProtectedRoute({ children, allowedRole = null }) {
  const location = useLocation();
  const userRole = sessionStorage.getItem('vignan_user_role');
  const userId = sessionStorage.getItem('vignan_user_id');

  // 1. Check if ANY user is logged in
  if (!userRole || !userId) {
    console.warn(`[AuthGuard] Generic Block: No valid session found. Redirecting to Login.`);
    return <Navigate to="/" state={{ from: location }} replace />;
  }

  // 2. Role-based check (if specified)
  if (allowedRole && userRole !== allowedRole) {
    console.error(`[AuthGuard] Permission Denied: Role '${userRole}' cannot access '${allowedRole}' area.`);
    return <Navigate to="/" replace />;
  }

  return children;
}
