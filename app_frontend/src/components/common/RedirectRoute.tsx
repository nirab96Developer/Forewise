// RedirectRoute component - handles redirects based on auth state
import React from "react";
import { Navigate } from "react-router-dom";

interface RedirectRouteProps {
  to: string;
  children?: React.ReactNode;
}

const RedirectRoute: React.FC<RedirectRouteProps> = ({ to }) => {
  return <Navigate to={to} replace />;
};

export default RedirectRoute;
