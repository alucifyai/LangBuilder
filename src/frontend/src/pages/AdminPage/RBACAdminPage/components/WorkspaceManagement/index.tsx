import { useState } from "react";

export default function WorkspaceManagement() {
  const [workspaces] = useState([
    { id: "1", name: "Default Workspace", members: 5, projects: 3, status: "Active" },
    { id: "2", name: "Development", members: 8, projects: 7, status: "Active" },
    { id: "3", name: "Testing", members: 3, projects: 2, status: "Inactive" },
  ]);

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold">Workspace Management</h2>
        <button className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">
          Create Workspace
        </button>
      </div>

      <div className="mb-4">
        <input
          type="text"
          placeholder="Search workspaces..."
          className="border rounded px-3 py-2 w-64"
        />
      </div>

      <div className="border rounded-lg overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Name</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Members</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Projects</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Status</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {workspaces.map((workspace) => (
              <tr key={workspace.id} className="hover:bg-gray-50">
                <td className="px-4 py-3 font-medium">{workspace.name}</td>
                <td className="px-4 py-3">{workspace.members}</td>
                <td className="px-4 py-3">{workspace.projects}</td>
                <td className="px-4 py-3">
                  <span className={`px-2 py-1 rounded text-xs ${
                    workspace.status === "Active"
                      ? "bg-green-100 text-green-800"
                      : "bg-gray-100 text-gray-800"
                  }`}>
                    {workspace.status}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <div className="flex space-x-2">
                    <button className="text-blue-600 hover:text-blue-800 text-sm">Edit</button>
                    <button className="text-red-600 hover:text-red-800 text-sm">Delete</button>
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