import React, { createContext, useContext, useReducer, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import { api } from '../services/api';

interface User {
  id: string;
  username: string;
  email: string;
  role: string;
  permissions: string[];
}

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}

type AuthAction =
  | { type: 'LOGIN_START' }
  | { type: 'LOGIN_SUCCESS'; payload: { user: User; token: string } }
  | { type: 'LOGIN_FAILURE'; payload: string }
  | { type: 'LOGOUT' }
  | { type: 'LOAD_USER'; payload: User };

interface AuthContextType extends AuthState {
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  hasPermission: (permission: string) => boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const initialState: AuthState = {
  user: null,
  token: localStorage.getItem('token'),
  isAuthenticated: false,
  isLoading: true,
};

function authReducer(state: AuthState, action: AuthAction): AuthState {
  switch (action.type) {
    case 'LOGIN_START':
      return {
        ...state,
        isLoading: true,
      };
    case 'LOGIN_SUCCESS':
      localStorage.setItem('token', action.payload.token);
      return {
        ...state,
        user: action.payload.user,
        token: action.payload.token,
        isAuthenticated: true,
        isLoading: false,
      };
    case 'LOGIN_FAILURE':
      return {
        ...state,
        user: null,
        token: null,
        isAuthenticated: false,
        isLoading: false,
      };
    case 'LOGOUT':
      localStorage.removeItem('token');
      return {
        ...state,
        user: null,
        token: null,
        isAuthenticated: false,
        isLoading: false,
      };
    case 'LOAD_USER':
      return {
        ...state,
        user: action.payload,
        isAuthenticated: true,
        isLoading: false,
      };
    default:
      return state;
  }
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [state, dispatch] = useReducer(authReducer, initialState);
  const navigate = useNavigate();

  useEffect(() => {
    const loadUser = async () => {
      if (state.token) {
        try {
          const response = await api.post('/auth/verify', { token: state.token });
          if (response.data.valid) {
            dispatch({
              type: 'LOAD_USER',
              payload: {
                id: response.data.user_id,
                username: response.data.user_id,
                email: `${response.data.user_id}@smartcloudops.ai`,
                role: response.data.role,
                permissions: response.data.permissions,
              },
            });
          } else {
            dispatch({ type: 'LOGOUT' });
          }
        } catch (error) {
          dispatch({ type: 'LOGOUT' });
        }
      } else {
        dispatch({ type: 'LOGOUT' });
      }
    };

    loadUser();
  }, [state.token]);

  const login = async (username: string, password: string) => {
    dispatch({ type: 'LOGIN_START' });
    
    try {
      const response = await api.post('/auth/login', { username, password });
      const { token, user_id, role, permissions } = response.data;
      
      dispatch({
        type: 'LOGIN_SUCCESS',
        payload: {
          user: {
            id: user_id,
            username,
            email: `${username}@smartcloudops.ai`,
            role,
            permissions,
          },
          token,
        },
      });
      
      toast.success('Login successful!');
      navigate('/');
    } catch (error: any) {
      const message = error.response?.data?.error || 'Login failed';
      dispatch({ type: 'LOGIN_FAILURE', payload: message });
      toast.error(message);
    }
  };

  const logout = () => {
    dispatch({ type: 'LOGOUT' });
    navigate('/login');
    toast.success('Logged out successfully');
  };

  const hasPermission = (permission: string): boolean => {
    return state.user?.permissions.includes(permission) || false;
  };

  const value: AuthContextType = {
    ...state,
    login,
    logout,
    hasPermission,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
