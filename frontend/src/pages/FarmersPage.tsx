import React, { useEffect, useState } from 'react';
import {
  Users,
  UserPlus,
  Search,
  Edit2,
  Trash2,
  Phone,
  Mail,
  MapPin,
  CheckCircle2,
  AlertCircle,
  X,
  RefreshCw,
} from 'lucide-react';
import { getFarmers, getFarmer, createFarmer, updateFarmer, deleteFarmer, getErrorMessage } from '../services/api';
import type { Farmer, FarmerCreate, FarmerUpdate, Field } from '../types';

export const FarmersPage: React.FC = () => {
  const [farmers, setFarmers] = useState<Farmer[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Modals state
  const [showAddModal, setShowAddModal] = useState(false);
  const [editingFarmer, setEditingFarmer] = useState<Farmer | null>(null);
  const [viewingFarmer, setViewingFarmer] = useState<(Farmer & { fields: Field[] }) | null>(null);

  // Form state
  const [formData, setFormData] = useState<FarmerCreate>({
    name: '',
    phone: '',
    email: '',
  });
  const [submitting, setSubmitting] = useState(false);

  const fetchFarmers = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getFarmers();
      setFarmers(data);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchFarmers();
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.name.trim()) return;
    try {
      setSubmitting(true);
      setError(null);
      await createFarmer(formData);
      setSuccess('Farmer registered successfully!');
      setTimeout(() => setSuccess(null), 3000);
      setShowAddModal(false);
      setFormData({ name: '', phone: '', email: '' });
      await fetchFarmers();
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  };

  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingFarmer) return;
    try {
      setSubmitting(true);
      setError(null);
      await updateFarmer(editingFarmer.farmer_id, {
        name: editingFarmer.name,
        phone: editingFarmer.phone || undefined,
        email: editingFarmer.email || undefined,
      });
      setSuccess('Farmer details updated.');
      setTimeout(() => setSuccess(null), 3000);
      setEditingFarmer(null);
      await fetchFarmers();
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (farmer: Farmer) => {
    const msg = `Are you sure you want to delete farmer '${farmer.name}' (${farmer.farmer_id})? This will also remove any associated fields and sensors.`;
    if (!window.confirm(msg)) return;
    try {
      setError(null);
      await deleteFarmer(farmer.farmer_id);
      setSuccess(`Farmer '${farmer.name}' deleted.`);
      setTimeout(() => setSuccess(null), 3000);
      await fetchFarmers();
    } catch (err) {
      setError(getErrorMessage(err));
    }
  };

  const handleView = async (farmerId: string) => {
    try {
      const details = await getFarmer(farmerId);
      setViewingFarmer(details);
    } catch (err) {
      setError(getErrorMessage(err));
    }
  };

  const filteredFarmers = farmers.filter(
    (f) =>
      f.name.toLowerCase().includes(search.toLowerCase()) ||
      f.farmer_id.toLowerCase().includes(search.toLowerCase()) ||
      (f.phone && f.phone.includes(search)) ||
      (f.email && f.email.toLowerCase().includes(search.toLowerCase()))
  );

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Farmer Management</h1>
          <p className="text-sm text-slate-500 mt-1">
            Register and manage farm owners, contact coordinates, and linked agricultural fields.
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setShowAddModal(true)}
            className="inline-flex items-center space-x-1.5 px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold rounded-xl shadow-xs transition-colors"
          >
            <UserPlus className="w-4 h-4" />
            <span>Add Farmer</span>
          </button>
          <button
            onClick={fetchFarmers}
            className="p-2 bg-white hover:bg-slate-50 border border-slate-200 text-slate-600 rounded-xl transition-colors"
            title="Refresh list"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Notifications */}
      {error && (
        <div className="p-3.5 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 text-rose-500 shrink-0" />
            <span>{error}</span>
          </div>
          <button onClick={() => setError(null)}><X className="w-4 h-4" /></button>
        </div>
      )}
      {success && (
        <div className="p-3.5 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
            <span>{success}</span>
          </div>
          <button onClick={() => setSuccess(null)}><X className="w-4 h-4" /></button>
        </div>
      )}

      {/* Search and Filters Bar */}
      <div className="bg-white p-3 rounded-2xl border border-slate-200/80 shadow-xs flex items-center space-x-3">
        <Search className="w-4 h-4 text-slate-400 ml-2" />
        <input
          type="text"
          placeholder="Search by name, ID (e.g. FR001), phone, or email..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full text-xs bg-transparent border-0 focus:outline-none text-slate-800 placeholder-slate-400"
        />
        {search && (
          <button onClick={() => setSearch('')} className="text-slate-400 hover:text-slate-600 text-xs px-2">
            Clear
          </button>
        )}
      </div>

      {/* Farmers Table */}
      <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-100 text-slate-500 font-semibold uppercase tracking-wider">
                <th className="py-3 px-4">Farmer ID</th>
                <th className="py-3 px-4">Name</th>
                <th className="py-3 px-4">Phone</th>
                <th className="py-3 px-4">Email</th>
                <th className="py-3 px-4">Origin</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-700">
              {filteredFarmers.map((f) => (
                <tr key={f.farmer_id} className="hover:bg-slate-50/70 transition-colors">
                  <td className="py-3 px-4 font-mono font-medium text-emerald-700">{f.farmer_id}</td>
                  <td className="py-3 px-4 font-semibold text-slate-900">{f.name}</td>
                  <td className="py-3 px-4 text-slate-600">
                    {f.phone ? (
                      <span className="inline-flex items-center space-x-1">
                        <Phone className="w-3 h-3 text-slate-400" />
                        <span>{f.phone}</span>
                      </span>
                    ) : (
                      <span className="text-slate-400">—</span>
                    )}
                  </td>
                  <td className="py-3 px-4 text-slate-600">
                    {f.email ? (
                      <span className="inline-flex items-center space-x-1">
                        <Mail className="w-3 h-3 text-slate-400" />
                        <span>{f.email}</span>
                      </span>
                    ) : (
                      <span className="text-slate-400">—</span>
                    )}
                  </td>
                  <td className="py-3 px-4">
                    {f.is_demo ? (
                      <span className="inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-medium bg-amber-50 text-amber-700 border border-amber-200">
                        Demo
                      </span>
                    ) : (
                      <span className="inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">
                        Live Farmer
                      </span>
                    )}
                  </td>
                  <td className="py-3 px-4 text-right space-x-2">
                    <button
                      onClick={() => handleView(f.farmer_id)}
                      className="px-2.5 py-1 text-slate-600 hover:text-emerald-700 font-medium hover:bg-slate-100 rounded-lg transition-colors"
                    >
                      Fields
                    </button>
                    <button
                      onClick={() => setEditingFarmer(f)}
                      className="p-1.5 text-slate-500 hover:text-emerald-700 hover:bg-slate-100 rounded-lg transition-colors"
                      title="Edit farmer"
                    >
                      <Edit2 className="w-3.5 h-3.5" />
                    </button>
                    <button
                      onClick={() => handleDelete(f)}
                      className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-colors"
                      title="Delete farmer"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </td>
                </tr>
              ))}
              {filteredFarmers.length === 0 && !loading && (
                <tr>
                  <td colSpan={6} className="text-center py-8 text-slate-400">
                    {search ? 'No farmers match your search filter.' : 'No farmers registered yet. Click "Add Farmer" above.'}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Add Farmer Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-xl border border-slate-200">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-4">
              <h3 className="font-bold text-slate-900 text-sm">Register New Farmer</h3>
              <button onClick={() => setShowAddModal(false)}><X className="w-4 h-4 text-slate-400" /></button>
            </div>
            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Farmer Full Name *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Harini Devi"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full text-xs p-2.5 rounded-xl border border-slate-200 focus:outline-emerald-600"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Contact Phone</label>
                <input
                  type="text"
                  placeholder="e.g. 9876543210"
                  value={formData.phone}
                  onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                  className="w-full text-xs p-2.5 rounded-xl border border-slate-200 focus:outline-emerald-600"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Email Address</label>
                <input
                  type="email"
                  placeholder="e.g. harini@example.com"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  className="w-full text-xs p-2.5 rounded-xl border border-slate-200 focus:outline-emerald-600"
                />
              </div>
              <div className="flex justify-end space-x-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="px-4 py-2 text-xs text-slate-600 hover:bg-slate-100 rounded-xl"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-4 py-2 text-xs font-semibold text-white bg-emerald-600 hover:bg-emerald-700 rounded-xl"
                >
                  {submitting ? 'Saving...' : 'Register Farmer'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit Farmer Modal */}
      {editingFarmer && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-xl border border-slate-200">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-4">
              <h3 className="font-bold text-slate-900 text-sm">Edit Farmer ({editingFarmer.farmer_id})</h3>
              <button onClick={() => setEditingFarmer(null)}><X className="w-4 h-4 text-slate-400" /></button>
            </div>
            <form onSubmit={handleUpdate} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Full Name</label>
                <input
                  type="text"
                  required
                  value={editingFarmer.name}
                  onChange={(e) => setEditingFarmer({ ...editingFarmer, name: e.target.value })}
                  className="w-full text-xs p-2.5 rounded-xl border border-slate-200 focus:outline-emerald-600"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Phone</label>
                <input
                  type="text"
                  value={editingFarmer.phone || ''}
                  onChange={(e) => setEditingFarmer({ ...editingFarmer, phone: e.target.value })}
                  className="w-full text-xs p-2.5 rounded-xl border border-slate-200 focus:outline-emerald-600"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Email</label>
                <input
                  type="email"
                  value={editingFarmer.email || ''}
                  onChange={(e) => setEditingFarmer({ ...editingFarmer, email: e.target.value })}
                  className="w-full text-xs p-2.5 rounded-xl border border-slate-200 focus:outline-emerald-600"
                />
              </div>
              <div className="flex justify-end space-x-2 pt-2">
                <button
                  type="button"
                  onClick={() => setEditingFarmer(null)}
                  className="px-4 py-2 text-xs text-slate-600 hover:bg-slate-100 rounded-xl"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-4 py-2 text-xs font-semibold text-white bg-emerald-600 hover:bg-emerald-700 rounded-xl"
                >
                  {submitting ? 'Updating...' : 'Save Changes'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* View Associated Fields Modal */}
      {viewingFarmer && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-xl border border-slate-200">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-4">
              <div>
                <h3 className="font-bold text-slate-900 text-sm">Associated Fields</h3>
                <p className="text-xs text-slate-500">Owned by {viewingFarmer.name} ({viewingFarmer.farmer_id})</p>
              </div>
              <button onClick={() => setViewingFarmer(null)}><X className="w-4 h-4 text-slate-400" /></button>
            </div>
            <div className="space-y-3 max-h-80 overflow-y-auto">
              {viewingFarmer.fields && viewingFarmer.fields.length > 0 ? (
                viewingFarmer.fields.map((fld) => (
                  <div key={fld.field_id} className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 text-xs">
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-bold text-slate-900">{fld.name} ({fld.field_id})</span>
                      <span className="px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 font-medium text-[10px]">
                        {fld.crop_type}
                      </span>
                    </div>
                    <div className="text-slate-500 text-[11px] flex items-center space-x-2">
                      <MapPin className="w-3 h-3 text-slate-400" />
                      <span>{fld.location_name || 'No location name'} ({fld.area_hectares || 0} ha)</span>
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-center py-6 text-xs text-slate-400">
                  No fields assigned to this farmer yet.
                </div>
              )}
            </div>
            <div className="mt-4 flex justify-end">
              <button
                onClick={() => setViewingFarmer(null)}
                className="px-4 py-2 text-xs font-semibold bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
