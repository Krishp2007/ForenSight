import React, { createContext, useState, useEffect, useContext } from 'react';
import apiClient from '../services/apiClient';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Parse user status on app mount if token is saved
  useEffect(() => {
    const initializeAuth = async () => {
      const token = localStorage.getItem('token');
      if (token) {
        try {
          const res = await apiClient.get('/auth/me');
          setUser(res.data);
        } catch (err) {
          console.error("Token restoration failed", err);
          localStorage.removeItem('token');
          setUser(null);
        }
      }
      setLoading(false);
    };

    initializeAuth();
  }, []);

  const login = async (email, password) => {
    setLoading(true);
    try {
      // OAuth2 password grant type expects x-www-form-urlencoded
      const formData = new URLSearchParams();
      formData.append('username', email);
      formData.append('password', password);

      const response = await apiClient.post('/auth/login', formData, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      });

      const { access_token } = response.data;
      localStorage.setItem('token', access_token);

      // Pull user profile details
      const profileRes = await apiClient.get('/auth/me');
      setUser(profileRes.data);
      setLoading(false);
      return profileRes.data;
    } catch (err) {
      setLoading(false);
      throw err.response?.data?.detail || 'Incorrect credentials or server offline.';
    }
  };

  const registerUser = async (email, username, organization_id, password, role = 'investigator') => {
    setLoading(true);
    try {
      const response = await apiClient.post('/auth/register', {
        email,
        username,
        organization_id,
        password,
        role: role.toLowerCase(),
      });
      setLoading(false);
      return response.data;
    } catch (err) {
      setLoading(false);
      throw err.response?.data?.detail || 'Registration failed.';
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        isAuthenticated: !!user,
        login,
        register: registerUser,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
