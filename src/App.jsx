import Home from "./components/Home";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Runout from "./components/Runout";
import Lbw from "./components/Lbw";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/runout" element={<Runout />} />
        <Route path="/lbw" element={<Lbw />} />
        <Route path="/" element={<Home />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
