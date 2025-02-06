import { useEffect, useState } from "react";
import '../styles/style.css';

const InstructorList = () => {
  const [instructors, setInstructors] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [editingInstructor, setEditingInstructor] = useState(null);
  const [newInstructor, setNewInstructor] = useState("");
  const [newIdNumber, setNewIdNumber] = useState("");
  const [newDept, setNewDept] = useState("");

  useEffect(() => {
    fetchInstructors();
  }, []);

  const fetchInstructors = () => {
    fetch("http://localhost:8001/instructor")
      .then((response) => response.json())
      .then((data) => setInstructors(data))
      .catch((error) => console.error("Error fetching instructors:", error));
  };

  const handleSave = async () => {
    if (!newInstructor.trim() || !newIdNumber.trim() || !newDept.trim()) return;

    try {
      const response = await fetch("http://localhost:8001/instructor" + (editingInstructor ? `/${editingInstructor.id_number}` : ""), {
        method: editingInstructor ? "PUT" : "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          id_number: newIdNumber,
          name: newInstructor,
          dept: newDept,
        }),
      });

      if (!response.ok) {
        throw new Error(editingInstructor ? "Failed to update instructor" : "Failed to add instructor");
      }

      setNewInstructor("");
      setNewIdNumber("");
      setNewDept("");
      setShowForm(false);
      setEditingInstructor(null);
      fetchInstructors();
    } catch (error) {
      console.error(error);
    }
  };

  const deleteInstructor = async (id_number) => {
    try {
      const response = await fetch(`http://localhost:8001/instructor/${id_number}`, {
        method: "DELETE",
      });

      if (!response.ok) {
        throw new Error("Failed to delete instructor");
      }

      fetchInstructors();
    } catch (error) {
      console.error("Error deleting instructor:", error);
    }
  };

  const handleEdit = (instructor) => {
    setEditingInstructor(instructor);
    setNewIdNumber(instructor.id_number);
    setNewInstructor(instructor.name);
    setNewDept(instructor.dept);
    setShowForm(true);
  };

  return (
    <div className="p-4">
      <h2 className="text-xl font-bold mb-4">Instructors</h2>
      <button onClick={() => setShowForm(true)} className="submit">
        Add Instructor
      </button>
      {showForm && (
        <div className="mb-4 p-4 border rounded bg-gray-100">
          <input
            type="text"
            value={newIdNumber}
            onChange={(e) => setNewIdNumber(e.target.value)}
            placeholder="Enter Instructor ID Number"
            className="p-2 border rounded w-full mb-2"
            disabled={editingInstructor}
          />
          <input
            type="text"
            value={newInstructor}
            onChange={(e) => setNewInstructor(e.target.value)}
            placeholder="Enter Instructor Name"
            className="p-2 border rounded w-full mb-2"
          />
          <input
            type="text"
            value={newDept}
            onChange={(e) => setNewDept(e.target.value)}
            placeholder="Enter Department"
            className="p-2 border rounded w-full mb-2"
          />
          <button onClick={handleSave} className="bg-green-500 text-white px-4 py-2 rounded">
            {editingInstructor ? "Update" : "Save"}
          </button>
          <button onClick={() => { setShowForm(false); setEditingInstructor(null); }} className="bg-red-500 text-white px-4 py-2 rounded ml-2">
            Cancel
          </button>
        </div>
      )}
      <table className="instructor-list table">
        <thead>
          <tr className="bg-gray-200">
            <th className="border border-gray-400 p-2">ID</th>
            <th className="border border-gray-400 p-2">Name</th>
            <th className="border border-gray-400 p-2">Department</th>
            <th className="border border-gray-400 p-2">Actions</th>
          </tr>
        </thead>
        <tbody>
          {instructors.map((instructor) => (
            <tr key={instructor.id_number} className="text-center">
              <td className="border border-gray-400 p-2">{instructor.id_number}</td>
              <td className="border border-gray-400 p-2">{instructor.name}</td>
              <td className="border border-gray-400 p-2">{instructor.dept}</td>
              <td className="border border-gray-400 p-2 space-x-2">
                <button onClick={() => handleEdit(instructor)} className="bg-blue-500 text-white px-3 py-1 rounded">
                  Edit
                </button>
                <button onClick={() => deleteInstructor(instructor.id_number)} className="bg-red-500 text-white px-3 py-1 rounded">
                  Delete
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default InstructorList;
