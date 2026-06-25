import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Navbar from './Components/Navbar';
import LoginPage from './Pages/Login';
import HomePage from './Pages/Home';
import CategoryPage from './Pages/Category';
import RecommendationPage from './Pages/Recommendation';
import OCRPage from './Pages/OCR';
import SummaryPage from './Pages/Summary';
import NotificationPage from './Pages/Notification';
import SupportPage from './Pages/Support';
import MypagePage from './Pages/Mypage';

function PrivateRoute({ children }) {
  const token = localStorage.getItem('token');
  return token ? children : <Navigate to="/login" replace />;
}

function Layout({ children }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div style={{ flex: 1, overflowY: 'auto' }}>
        {children}
      </div>
      <Navbar />
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route
          path="/"
          element={
            <PrivateRoute>
              <Layout><HomePage /></Layout>
            </PrivateRoute>
          }
        />
        <Route
          path="/category"
          element={
            <PrivateRoute>
              <Layout><CategoryPage /></Layout>
            </PrivateRoute>
          }
        />
        <Route
          path="/recommendation"
          element={
            <PrivateRoute>
              <RecommendationPage />
            </PrivateRoute>
          }
        />
        <Route
          path="/ocr"
          element={
            <PrivateRoute>
              <OCRPage />
            </PrivateRoute>
          }
        />
        <Route
          path="/summary"
          element={
            <PrivateRoute>
              <SummaryPage />
            </PrivateRoute>
          }
        />
        <Route
          path="/notification"
          element={
            <PrivateRoute>
              <NotificationPage />
            </PrivateRoute>
          }
        />
        <Route
          path="/support"
          element={
            <PrivateRoute>
              <Layout><SupportPage /></Layout>
            </PrivateRoute>
          }
        />
        <Route
          path="/mypage"
          element={
            <PrivateRoute>
              <Layout><MypagePage /></Layout>
            </PrivateRoute>
          }
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
