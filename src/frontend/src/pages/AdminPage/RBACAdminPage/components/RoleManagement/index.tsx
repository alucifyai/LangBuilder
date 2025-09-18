import { useState } from "react";

export default function RoleManagement() {
  const [roles] = useState([
    { id: "1", name: "Admin", description: "Full system access", users: 2, permissions: 15 },
    { id: "2", name: "Editor", description: "Content management access", users: 5, permissions: 8 },
    { id: "3", name: "Viewer", description: "Read-only access", users: 12, permissions: 3 },
  ]);

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold">Role Management</h2>
        <button className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">
          Create Role
        </button>
      </div>

      <div className="mb-4">
        <input
          type="text"
          placeholder="Search roles..."
          className="border rounded px-3 py-2 w-64"
        />
      </div>

      <div className="border rounded-lg overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Role Name</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Description</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Users</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Permissions</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {roles.map((role) => (
              <tr key={role.id} className="hover:bg-gray-50">
                <td className="px-4 py-3 font-medium">{role.name}</td>
                <td className="px-4 py-3 text-gray-600">{role.description}</td>
                <td className="px-4 py-3">{role.users}</td>
                <td className="px-4 py-3">{role.permissions}</td>
                <td className="px-4 py-3">
                  <div className="flex space-x-2">
                    <button className="text-blue-600 hover:text-blue-800 text-sm">Edit</button>
                    <button className="text-green-600 hover:text-green-800 text-sm">Permissions</button>
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