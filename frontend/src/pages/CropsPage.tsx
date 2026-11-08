import React, { useEffect, useState } from 'react';
import {
  Wheat,
  Plus,
  Search,
  Edit2,
  Trash2,
  RefreshCw,
  AlertCircle,
  CheckCircle2,
  X,
  Calendar,
  Layers,
} from 'lucide-react';
import {
  getCrops,
  getFields,
  createCrop,
  updateCrop,
  deleteCrop,
  getErrorMessage,
} from '../services/api';
import type { Crop, CropCreate, CropPatch, Field } from '../types';

export const CropsPage: React.FC = () => {
  const [crops, setCrops] = useState<Crop[]>([]);
  const [fields, setFields] = useState<Field[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [selectedFieldFilter, setSelectedFieldFilter] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Modal states
  const [showAddModal, setShowAddModal] = useState(false);
  const [editingCrop, setEditingCrop] = useState<Crop | null>(null);

  // Form states
  const [formData, setFormData] = useState<CropCreate>({
    field_id: '',
    crop_type: '',
    variety: '',
    planting_date: '',
    growth_stage: 'vegetative',
    notes: '',
  });
  const [submitting, setSubmitting] = useState(false);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [crpData, fldData] = await Promise.all([getCrops(), getFields()]);
      setCrops(crpData);
      setFields(fldData);
      if (fldData.length > 0 && !formData.field_id) {
        setFormData((prev) => ({ ...prev, field_id: fldData[0].field_id }));
      }
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.crop_type.trim() || !formData.field_id) return;
    try {
      setSubmitting(true);
      setError(null);
      await createCrop(formData);
      setSuccess('Crop record added.');
      setTimeout(() => setSuccess(null), 3000);
      setShowAddModal(false);
      setFormData({
        field_id: fields[0]?.field_id || '',
        crop_type: '',
        variety: '',
        planting_date: '',
        growth_stage: 'vegetative',
        notes: '',
      });
      await fetchData();
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  };

  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingCrop) return;
    try {
      setSubmitting(true);
      setError(null);
      await updateCrop(editingCrop.crop_id, {
        crop_type: editingCrop.crop_type,
        variety: editingCrop.variety || undefined,
        planting_date: editingCrop.planting_date || undefined,
        growth_stage: editingCrop.growth_stage || undefined,
        notes: editingCrop.notes || undefined,
        field_id: editingCrop.field_id,
      });
      setSuccess('Crop details updated.');
      setTimeout(() => setSuccess(null), 3000);
      setEditingCrop(null);
      await fetchData();
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (crop: Crop) => {
    if (!window.confirm(`Delete crop record '${crop.crop_type}' (${crop.crop_id})?`)) return;
    try {
      setError(null);
      await deleteCrop(crop.crop_id);
      setSuccess(`Crop record '${crop.crop_id}' deleted.`);
      setTimeout(() => setSuccess(null), 3000);
      await fetchData();
    } catch (err) {
      setError(getErrorMessage(err));
    }
  };

  const filteredCrops = crops.filter((c) => {
    const matchesSearch =
      c.crop_type.toLowerCase().includes(search.toLowerCase()) ||
      c.crop_id.toLowerCase().includes(search.toLowerCase()) ||
      (c.variety && c.variety.toLowerCase().includes(search.toLowerCase())) ||
      (c.growth_stage && c.growth_stage.toLowerCase().includes(search.toLowerCase()));
    const matchesField = selectedFieldFilter ? c.field_id === selectedFieldFilter : true;
    return matchesSearch && matchesField;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Crop Records &amp; Varieties</h1>
          <p className="text-sm text-slate-500 mt-1">
            Track planted crop species, agronomic stages, sowing dates, and field linkages.
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setShowAddModal(true)}
            disabled={fields.length === 0}
            className="inline-flex items-center space-x-1.5 px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold rounded-xl shadow-xs transition-colors disabled:opacity-50"
          >
            <Plus className="w-4 h-4" />
            <span>Add Crop</span>
          </button>
          <button
            onClick={fetchData}
            className="p-2 bg-white hover:bg-slate-50 border border-slate-200 text-slate-600 rounded-xl transition-colors"
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

      {/* Filter Bar */}
      <div className="bg-white p-3 rounded-2xl border border-slate-200/80 shadow-xs flex flex-col sm:flex-row items-center gap-3">
        <div className="flex-1 flex items-center space-x-2 w-full">
          <Search className="w-4 h-4 text-slate-400 ml-2" />
          <input
            type="text"
            placeholder="Search crop type, variety, ID, or stage..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full text-xs bg-transparent border-0 focus:outline-none text-slate-800 placeholder-slate-400"
          />
        </div>
        <div className="flex items-center space-x-2 w-full sm:w-auto">
          <select
            value={selectedFieldFilter}
            onChange={(e) => setSelectedFieldFilter(e.target.value)}
            className="text-xs p-2 rounded-xl border border-slate-200 bg-slate-50 text-slate-700 focus:outline-none"
          >
            <option value="">All Fields</option>
            {fields.map((fld) => (
              <option key={fld.field_id} value={fld.field_id}>
                {fld.name} ({fld.field_id})
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Table */}
      <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-100 text-slate-500 font-semibold uppercase tracking-wider">
                <th className="py-3 px-4">Crop ID</th>
                <th className="py-3 px-4">Crop Type</th>
                <th className="py-3 px-4">Field ID</th>
                <th className="py-3 px-4">Variety</th>
                <th className="py-3 px-4">Planting Date</th>
                <th className="py-3 px-4">Growth Stage</th>
                <th className="py-3 px-4">Notes</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-700">
              {filteredCrops.map((c) => (
                <tr key={c.crop_id} className="hover:bg-slate-50/70 transition-colors">
                  <td className="py-3 px-4 font-mono font-medium text-emerald-700">{c.crop_id}</td>
                  <td className="py-3 px-4 font-bold text-slate-900">{c.crop_type}</td>
                  <td className="py-3 px-4 font-mono text-[11px] text-slate-600">{c.field_id}</td>
                  <td className="py-3 px-4 text-slate-600">{c.variety || '—'}</td>
                  <td className="py-3 px-4 text-slate-600">
                    {c.planting_date ? (
                      <span className="inline-flex items-center space-x-1">
                        <Calendar className="w-3 h-3 text-slate-400" />
                        <span>{c.planting_date}</span>
                      </span>
                    ) : (
                      '—'
                    )}
                  </td>
                  <td className="py-3 px-4">
                    <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-medium bg-amber-50 text-amber-800 border border-amber-200">
                      {c.growth_stage || 'vegetative'}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-slate-500 max-w-xs truncate">{c.notes || '—'}</td>
                  <td className="py-3 px-4 text-right space-x-2">
                    <button
                      onClick={() => setEditingCrop(c)}
                      className="p-1.5 text-slate-500 hover:text-emerald-700 hover:bg-slate-100 rounded-lg transition-colors"
                      title="Edit crop"
                    >
                      <Edit2 className="w-3.5 h-3.5" />
                    </button>
                    <button
                      onClick={() => handleDelete(c)}
                      className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-colors"
                      title="Delete crop"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </td>
                </tr>
              ))}
              {filteredCrops.length === 0 && !loading && (
                <tr>
                  <td colSpan={8} className="text-center py-8 text-slate-400">
                    {search ? 'No crops match search criteria.' : 'No crop records added yet.'}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Add Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-xl border border-slate-200">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-4">
              <h3 className="font-bold text-slate-900 text-sm">Add Crop Record</h3>
              <button onClick={() => setShowAddModal(false)}><X className="w-4 h-4 text-slate-400" /></button>
            </div>
            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Field *</label>
                <select
                  required
                  value={formData.field_id}
                  onChange={(e) => setFormData({ ...formData, field_id: e.target.value })}
                  className="w-full text-xs p-2.5 rounded-xl border border-slate-200 focus:outline-emerald-600 bg-white"
                >
                  {fields.map((fld) => (
                    <option key={fld.field_id} value={fld.field_id}>
                      {fld.name} ({fld.field_id})
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Crop Type *</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Maize"
                    value={formData.crop_type}
                    onChange={(e) => setFormData({ ...formData, crop_type: e.target.value })}
                    className="w-full text-xs p-2.5 rounded-xl border border-slate-200 focus:outline-emerald-600"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Variety</label>
                  <input
                    type="text"
                    placeholder="e.g. Pioneer 3302"
                    value={formData.variety || ''}
                    onChange={(e) => setFormData({ ...formData, variety: e.target.value })}
                    className="w-full text-xs p-2.5 rounded-xl border border-slate-200 focus:outline-emerald-600"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Planting Date</label>
                  <input
                    type="date"
                    value={formData.planting_date || ''}
                    onChange={(e) => setFormData({ ...formData, planting_date: e.target.value })}
                    className="w-full text-xs p-2.5 rounded-xl border border-slate-200 focus:outline-emerald-600"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Growth Stage</label>
                  <select
                    value={formData.growth_stage || 'vegetative'}
                    onChange={(e) => setFormData({ ...formData, growth_stage: e.target.value })}
                    className="w-full text-xs p-2.5 rounded-xl border border-slate-200 focus:outline-emerald-600 bg-white"
                  >
                    <option value="initial">Initial / Germination</option>
                    <option value="vegetative">Vegetative</option>
                    <option value="flowering">Flowering</option>
                    <option value="fruiting">Fruiting / Maturation</option>
                    <option value="harvest">Ready for Harvest</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Field Notes</label>
                <textarea
                  rows={2}
                  placeholder="Optional agronomic notes..."
                  value={formData.notes || ''}
                  onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
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
                  {submitting ? 'Adding...' : 'Save Crop'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit Modal */}
      {editingCrop && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-xl border border-slate-200">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-4">
              <h3 className="font-bold text-slate-900 text-sm">Edit Crop ({editingCrop.crop_id})</h3>
              <button onClick={() => setEditingCrop(null)}><X className="w-4 h-4 text-slate-400" /></button>
            </div>
            <form onSubmit={handleUpdate} className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Crop Type</label>
                  <input
                    type="text"
                    required
                    value={editingCrop.crop_type}
                    onChange={(e) => setEditingCrop({ ...editingCrop, crop_type: e.target.value })}
                    className="w-full text-xs p-2.5 rounded-xl border border-slate-200 focus:outline-emerald-600"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Variety</label>
                  <input
                    type="text"
                    value={editingCrop.variety || ''}
                    onChange={(e) => setEditingCrop({ ...editingCrop, variety: e.target.value })}
                    className="w-full text-xs p-2.5 rounded-xl border border-slate-200 focus:outline-emerald-600"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Planting Date</label>
                  <input
                    type="date"
                    value={editingCrop.planting_date || ''}
                    onChange={(e) => setEditingCrop({ ...editingCrop, planting_date: e.target.value })}
                    className="w-full text-xs p-2.5 rounded-xl border border-slate-200 focus:outline-emerald-600"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Growth Stage</label>
                  <select
                    value={editingCrop.growth_stage || 'vegetative'}
                    onChange={(e) => setEditingCrop({ ...editingCrop, growth_stage: e.target.value })}
                    className="w-full text-xs p-2.5 rounded-xl border border-slate-200 focus:outline-emerald-600 bg-white"
                  >
                    <option value="initial">Initial / Germination</option>
                    <option value="vegetative">Vegetative</option>
                    <option value="flowering">Flowering</option>
                    <option value="fruiting">Fruiting / Maturation</option>
                    <option value="harvest">Ready for Harvest</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Notes</label>
                <textarea
                  rows={2}
                  value={editingCrop.notes || ''}
                  onChange={(e) => setEditingCrop({ ...editingCrop, notes: e.target.value })}
                  className="w-full text-xs p-2.5 rounded-xl border border-slate-200 focus:outline-emerald-600"
                />
              </div>

              <div className="flex justify-end space-x-2 pt-2">
                <button
                  type="button"
                  onClick={() => setEditingCrop(null)}
                  className="px-4 py-2 text-xs text-slate-600 hover:bg-slate-100 rounded-xl"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-4 py-2 text-xs font-semibold text-white bg-emerald-600 hover:bg-emerald-700 rounded-xl"
                >
                  {submitting ? 'Saving...' : 'Save Changes'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
