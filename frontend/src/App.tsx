import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Findings from './pages/Findings';
import LiveAudit from './pages/LiveAudit';
import RunHistory from './pages/RunHistory';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/findings" element={<Findings />} />
          <Route path="/live" element={<LiveAudit />} />
          <Route path="/runs" element={<RunHistory />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
