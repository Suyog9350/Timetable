import { Route, BrowserRouter as Router, Routes } from "react-router-dom";
import Navbar from "./components/Navbar"; // Adjust the path to your Navbar component
import Departments from "./pages/Departments"; // Adjust the path to your Departments component
import Home from "./pages/Homepage"; // Adjust the path to your Home component
import Instructors from "./pages/Instructors"; // Adjust the path to your Instructors component
import Subjects from "./pages/Subjects"; // Adjust the path to your Subjects component
import Timetable from "./pages/Timetable";
import './styles/style.css';

function App() {
  return (
    <Router>
      <Navbar />
      <Routes>
        <Route path="/homepage" element={<Home />} />
        <Route path="/instructors" element={<Instructors />} />
        <Route path="/subjects" element={<Subjects />} />
        <Route path="/departments" element={<Departments />} />
        <Route path="/timetable" element={<Timetable />} />
      </Routes>
    </Router>
  );
}

export default App;
