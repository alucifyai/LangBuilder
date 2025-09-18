import { useState } from "react";

export default function UserAssignment() {
  const [assignments] = useState([
    { id: "1", user: "john.doe@example.com", role: "Admin", workspace: "Default", status: "Active", expires: "Never" },
    { id: "2", user: "jane.smith@example.com", role: "Editor", workspace: "Development", status: "Active", expires: "2024-12-31" },
    { id: "3", user: "bob.johnson@example.com", role: "Viewer", workspace: "Testing", status: "Inactive", expires: "2024-06-30" },
  ]);

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold">User Assignments</h2>
        <button className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">
          Assign Role
        </button>
      </div>

      <div className="flex space-x-4 mb-4">
        <input
          type="text"
          placeholder="Search users..."
          className="border rounded px-3 py-2 w-64"
        />
        <select className="border rounded px-3 py-2">
          <option value="">All Workspaces</option>
          <option value="default">Default</option>
          <option value="development">Development</option>
          <option value="testing">Testing</option>
        </select>
      </div>

      <div className="border rounded-lg overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">User</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Role</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Workspace</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Status</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Expires</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {assignments.map((assignment) => (
              <tr key={assignment.id} className="hover:bg-gray-50">
                <td className="px-4 py-3 font-medium">{assignment.user}</td>
                <td className="px-4 py-3">
                  <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs">
                    {assignment.role}
                  </span>
                </td>
                <td className="px-4 py-3">{assignment.workspace}</td>
                <td className="px-4 py-3">
                  <span className={`px-2 py-1 rounded text-xs ${
                    assignment.status === "Active"
                      ? "bg-green-100 text-green-800"
                      : "bg-gray-100 text-gray-800"
                  }`}>
                    {assignment.status}
                  </span>
                </td>
                <td className="px-4 py-3 text-gray-600">{assignment.expires}</td>
                <td className="px-4 py-3">
                  <div className="flex space-x-2">
                    <button className="text-blue-600 hover:text-blue-800 text-sm">Edit</button>
                    <button className="text-red-600 hover:text-red-800 text-sm">Remove</button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}