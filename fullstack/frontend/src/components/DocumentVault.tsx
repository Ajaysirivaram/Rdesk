/**
 * Component: components\DocumentVault.tsx
 * Purpose: Defines UI structure and behavior for this view/component.
 */
import React, { useEffect, useState } from 'react';
import { format, parseISO } from 'date-fns';
import { Upload, Download, Trash2, FileText } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { getJson, hrmsApi } from '@/services/hrmsApi';

interface Document {
  id: number;
  document_type: string;
  document_name: string;
  uploaded_at: string;
  file_url: string;
}

const DocumentVault: React.FC = () => {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [filterType, setFilterType] = useState<string>('ALL');
  
  const [formData, setFormData] = useState({
    document_type: '',
    document_name: '',
  });
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const docTypes = [
    'PAN', 'AADHAAR', 'BANK_DOC', 'CERTIFICATE',
    'OFFER_LETTER', 'APPOINTMENT_LETTER', 'PROMOTION_LETTER', 'PAYSLIP', 'OTHER'
  ];

  const docTypeLabels: Record<string, string> = {
    PAN: 'PAN Card',
    AADHAAR: 'Aadhaar',
    BANK_DOC: 'Bank Document',
    CERTIFICATE: 'Certificate',
    OFFER_LETTER: 'Offer Letter',
    APPOINTMENT_LETTER: 'Appointment Letter',
    PROMOTION_LETTER: 'Promotion Letter',
    PAYSLIP: 'Payslip',
    OTHER: 'Other',
  };

  useEffect(() => {
    loadDocuments();
  }, []);

  const loadDocuments = async () => {
    try {
      setLoading(true);
      setError('');
      const res = await hrmsApi.getDocuments();
      if (res.ok) {
        const data = await getJson<{ documents?: Document[] }>(res);
        setDocuments(data.documents || []);
      } else {
        setError('Failed to load documents');
      }
    } catch (err) {
      setError('Failed to load documents');
    } finally {
      setLoading(false);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      if (file.size > 10 * 1024 * 1024) {
        setError('File size exceeds 10MB limit');
        return;
      }
      setSelectedFile(file);
      setFormData({ ...formData, document_name: file.name });
    }
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (!selectedFile || !formData.document_type) {
        setError('Please select file and document type');
        return;
      }

      setLoading(true);
      setError('');

      const payload = new FormData();
      payload.append('file', selectedFile);
      payload.append('document_type', formData.document_type);
      payload.append('document_name', formData.document_name);

      const res = await hrmsApi.uploadDocument(payload);
      const data = await getJson<{ success?: boolean; message?: string }>(res);

      if (res.ok && data.success !== false) {
        setSuccess('Document uploaded successfully');
        setFormData({ document_type: '', document_name: '' });
        setSelectedFile(null);
        loadDocuments();
        setTimeout(() => setSuccess(''), 3000);
      } else {
        setError(data.message || 'Upload failed');
      }
    } catch (err) {
      setError('An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (docId: number) => {
    if (!confirm('Are you sure you want to delete this document?')) return;

    try {
      setError('');
      const res = await hrmsApi.deleteDocument(docId);

      if (res.ok) {
        setSuccess('Document deleted successfully');
        loadDocuments();
        setTimeout(() => setSuccess(''), 3000);
      } else {
        setError('Failed to delete document');
      }
    } catch (err) {
      setError('An error occurred');
    }
  };

  const handleDownload = async (docId: number, docName: string) => {
    try {
      setError('');
      const res = await hrmsApi.downloadDocument(docId);
      if (res.ok) {
        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = docName;
        a.click();
        window.URL.revokeObjectURL(url);
      }
    } catch (err) {
      setError('Failed to download document');
    }
  };

  const filteredDocs = filterType === 'ALL'
    ? documents
    : documents.filter(doc => doc.document_type === docTypeLabels[filterType as keyof typeof docTypeLabels]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <h2 className="text-2xl font-bold text-gray-900">Document Vault</h2>

      {/* Alerts */}
      {error && <Alert className="bg-red-50 border-red-200"><AlertDescription className="text-red-700">{error}</AlertDescription></Alert>}
      {success && <Alert className="bg-green-50 border-green-200"><AlertDescription className="text-green-700">{success}</AlertDescription></Alert>}

      {/* Upload Form */}
      <div className="bg-white p-6 rounded-lg border border-gray-200 shadow">
        <h3 className="text-lg font-semibold mb-4">Upload Document</h3>
        <form onSubmit={handleUpload} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Document Type *</label>
              <select
                value={formData.document_type}
                onChange={(e) => setFormData({ ...formData, document_type: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required
              >
                <option value="">Select Document Type</option>
                {docTypes.map(type => (
                  <option key={type} value={type}>{docTypeLabels[type]}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">File Name</label>
              <input
                type="text"
                value={formData.document_name}
                onChange={(e) => setFormData({ ...formData, document_name: e.target.value })}
                placeholder="Document name"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>

          <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
            <input
              type="file"
              onChange={handleFileSelect}
              className="hidden"
              id="file-input"
            />
            <label htmlFor="file-input" className="cursor-pointer">
              <Upload className="w-8 h-8 mx-auto mb-2 text-gray-400" />
              <p className="text-sm text-gray-600">
                {selectedFile ? selectedFile.name : 'Click to select or drag and drop'}
              </p>
              <p className="text-xs text-gray-500">Max 10MB</p>
            </label>
          </div>

          <div className="flex gap-3">
            <button
              type="submit"
              disabled={loading || !selectedFile}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2"
            >
              <Upload className="w-4 h-4" />
              {loading ? 'Uploading...' : 'Upload Document'}
            </button>
          </div>
        </form>
      </div>

      {/* Filter */}
      <div className="flex gap-2 overflow-x-auto pb-2">
        {['ALL', ...docTypes].map(type => (
          <button
            key={type}
            onClick={() => setFilterType(type)}
            className={`px-4 py-2 rounded-lg font-medium whitespace-nowrap ${
              filterType === type
                ? 'bg-blue-600 text-white'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            {type === 'ALL' ? 'All Documents' : docTypeLabels[type as keyof typeof docTypeLabels]}
          </button>
        ))}
      </div>

      {/* Documents List */}
      <div className="grid gap-4">
        {filteredDocs.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            No documents found
          </div>
        ) : (
          filteredDocs.map(doc => (
            <div key={doc.id} className="bg-white p-4 rounded-lg border border-gray-200 hover:border-blue-300 transition flex items-center justify-between">
              <div className="flex items-center gap-3 flex-1">
                <FileText className="w-6 h-6 text-blue-600" />
                <div>
                  <h4 className="font-semibold text-gray-900">{doc.document_name}</h4>
                  <p className="text-sm text-gray-600">{doc.document_type}</p>
                  <p className="text-xs text-gray-500">Uploaded {format(parseISO(doc.uploaded_at), 'MMM dd, yyyy')}</p>
                </div>
              </div>

              <div className="flex gap-2">
                <button
                  onClick={() => handleDownload(doc.id, doc.document_name)}
                  className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg transition"
                  title="Download"
                >
                  <Download className="w-5 h-5" />
                </button>
                <button
                  onClick={() => handleDelete(doc.id)}
                  className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition"
                  title="Delete"
                >
                  <Trash2 className="w-5 h-5" />
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default DocumentVault;

