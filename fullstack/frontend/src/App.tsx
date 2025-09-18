import { Suspense } from "react";
import { useRoutes, Routes, Route } from "react-router-dom";
import { AuthProvider } from "./contexts/AuthContext";
import ProtectedRoute from "./components/ProtectedRoute";
import Login from "./components/Login";
import Register from "./components/Register";
import Home from "./components/home";
import routes from "tempo-routes";

function TempoRoutes() {
  return useRoutes(routes);
}

function App() {
  const showTempoRoutes = import.meta.env.VITE_TEMPO === "true";

  return (
    <AuthProvider>
      <Suspense fallback={<p>Loading...</p>}>
        <>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route 
              path="/" 
              element={
                <ProtectedRoute>
                  <Home />
                </ProtectedRoute>
              } 
            />
          </Routes>
          {showTempoRoutes ? <TempoRoutes /> : null}
        </>
      </Suspense>
    </AuthProvider>
  );
}

export default App;
