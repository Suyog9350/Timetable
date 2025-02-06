import { Link } from "react-router-dom";
import '../styles/style.css';



const Navbar = () => {
  return (
    <div className="main">
      <div className="logo">
        <h1>WEEKLY TIMETABLE GENERATOR</h1>
        <h4>Create Timetable with a click </h4>
      </div>
      <nav>
        <ul>
          <li><Link to="/Homepage">Home</Link></li>
          <li><Link to="/Instructors">Instructor</Link></li>
          <li><Link to="/Subjects">Subjects</Link></li>
          <li><Link to="/Departments">Department</Link></li>
          <li><Link to="/Timetable">Timetable</Link></li>
        </ul>
      </nav>
    </div>
  );
};

export default Navbar;
