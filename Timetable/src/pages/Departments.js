import React, { useEffect, useState } from "react";
import '../styles/style.css';

const Departments = () => {
  const [departments, setDepartments] = useState([]);
  const [newDept, setNewDept] = useState("");
  const [editingDept, setEditingDept] = useState(null);
  const [editedDeptName, setEditedDeptName] = useState("");

  useEffect(() => {
    fetchDepartments();
  }, []);

  const fetchDepartments = async () => {
    try {
      const response = await fetch("http://localhost:8001/departments");
      if (!response.ok) throw new Error("Failed to fetch departments");
      const data = await response.json();
      setDepartments(data);
    } catch (error) {
      console.error("Error fetching departments:", error);
    }
  };

  const addDepartment = async () => {
    if (!newDept.trim()) return;
    try {
      const response = await fetch("http://localhost:8001/departments", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ dept_name: newDept }),
      });
      if (!response.ok) throw new Error("Failed to add department");
      setNewDept("");
      fetchDepartments();
    } catch (error) {
      console.error("Error adding department:", error);
    }
  };

  const deleteDepartment = async (deptName) => {
    try {
      const response = await fetch(`http://localhost:8001/departments/${deptName}`, {
        method: "DELETE",
      });
      if (!response.ok) throw new Error("Failed to delete department");
      fetchDepartments();
    } catch (error) {
      console.error("Error deleting department:", error);
    }
  };

  const editDepartment = async () => {
    if (!editedDeptName.trim() || !editingDept) return;
    try {
      const response = await fetch(`http://localhost:8001/departments/${editingDept}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ dept_name: editedDeptName }),
      });
      if (!response.ok) throw new Error("Failed to update department");
      setEditingDept(null);
      setEditedDeptName("");
      fetchDepartments();
    } catch (error) {
      console.error("Error updating department:", error);
    }
  };

  return (
    <div className="p-6 max-w-lg mx-auto">
      <h2 className="text-lg font-bold mb-4">Departments</h2>
      <div className="flex gap-2 mb-4">
        <input
          type="text"
          value={newDept}
          onChange={(e) => setNewDept(e.target.value)}
          placeholder="New Department Name"
          className="border p-2 flex-grow"
        />
        <button onClick={addDepartment} className="bg-green-500 text-white p-2 rounded">Add</button>
      </div>

      <table className="table-auto w-full border-collapse border border-gray-300">
        <thead>
          <tr className="bg-gray-100">
            <th className="border p-2">Department</th>
            <th className="border p-2">Actions</th>
          </tr>
        </thead>
        <tbody>
          {departments.length > 0 ? (
            departments.map((dept) => (
              <tr key={dept.dept_name} className="border-b">
                <td className="p-2">
                  {editingDept === dept.dept_name ? (
                    <input
                      type="text"
                      value={editedDeptName}
                      onChange={(e) => setEditedDeptName(e.target.value)}
                      className="border p-1"
                    />
                  ) : (
                    dept.dept_name
                  )}
                </td>
                <td className="p-2 flex gap-2">
                  {editingDept === dept.dept_name ? (
                    <button onClick={editDepartment} className="bg-blue-500 text-white p-1 rounded">Save</button>
                  ) : (
                    <button
                      onClick={() => { setEditingDept(dept.dept_name); setEditedDeptName(dept.dept_name); }}
                      className="bg-yellow-500 text-white p-1 rounded"
                    >
                      Edit
                    </button>
                  )}
                  <button onClick={() => deleteDepartment(dept.dept_name)} className="bg-red-500 text-white p-1 rounded">Delete</button>
                </td>
              </tr>
            ))
          ) : (
            <tr>
              <td className="text-gray-500 p-2 text-center" colSpan="2">No departments found.</td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
};

export default Departments;
