import React, { useState } from 'react';
import { Button } from './ui/button';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Alert, AlertDescription } from './ui/alert';
import { Progress } from './ui/progress';
import { Upload, FileSpreadsheet, CheckCircle, AlertCircle } from 'lucide-react';
import { monthlySalaryAPI } from '../services/api';

interface UploadResult {
  success: boolean;
  imported_count: number;
  updated_count: number;
  errors: string[];
  warnings: string[];
}

interface MonthlySalaryUploadProps {
  onSuccessNavigateToGenerate?: (period: { month: string; year: number }) => void;
}

const MonthlySalaryUpload: React.FC<MonthlySalaryUploadProps> = ({ onSuccessNavigateToGenerate }) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [month, setMonth] = useState('');
  const [year, setYear] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState<UploadResult | null>(null);
  const [progress, setProgress] = useState(0);

  const months = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'
  ];

  const currentYear = new Date().getFullYear();
  const years = Array.from({ length: 5 }, (_, i) => currentYear - 2 + i);

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      // Validate file type
      const validTypes = [
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', // .xlsx
        'application/vnd.ms-excel' // .xls
      ];
      
      if (!validTypes.includes(file.type)) {
        alert('Please select a valid Excel file (.xlsx or .xls)');
        return;
      }

      // Validate file size (10MB limit)
      if (file.size > 10 * 1024 * 1024) {
        alert('File size must be less than 10MB');
        return;
      }

      setSelectedFile(file);
      setUploadResult(null);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile || !month || !year) {
      alert('Please select a file, month, and year');
      return;
    }

    setIsUploading(true);
    setProgress(0);
    setUploadResult(null);

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('month', month);
      formData.append('year', year);

      // Simulate progress
      const progressInterval = setInterval(() => {
        setProgress(prev => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return 90;
          }
          return prev + 10;
        });
      }, 200);

      const response = await monthlySalaryAPI.uploadExcel(selectedFile, month, parseInt(year));

      clearInterval(progressInterval);
      setProgress(100);

      if (response.data.success) {
        setUploadResult(response.data);
        // Reset form
        const selectedMonth = month;
        const selectedYear = parseInt(year);
        setSelectedFile(null);
        setMonth('');
        setYear('');
        // Reset file input
        const fileInput = document.getElementById('file-upload') as HTMLInputElement;
        if (fileInput) fileInput.value = '';

        // Navigate to generate with prefilled period
        onSuccessNavigateToGenerate?.({ month: selectedMonth, year: selectedYear });
      } else {
        setUploadResult({
          success: false,
          imported_count: 0,
          updated_count: 0,
          errors: response.data.errors || ['Upload failed'],
          warnings: []
        });
      }
    } catch (error: any) {
      console.error('Upload error:', error);
      setUploadResult({
        success: false,
        imported_count: 0,
        updated_count: 0,
        errors: [error.response?.data?.message || 'Upload failed'],
        warnings: []
      });
    } finally {
      setIsUploading(false);
      setTimeout(() => setProgress(0), 2000);
    }
  };


  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileSpreadsheet className="h-5 w-5" />
            Upload Monthly Salary Data
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* File Upload */}
          <div className="space-y-2">
            <Label htmlFor="file-upload">Select Excel File</Label>
            <div className="flex items-center gap-4">
              <Input
                id="file-upload"
                type="file"
                accept=".xlsx,.xls"
                onChange={handleFileSelect}
                className="flex-1"
              />
            </div>
            {selectedFile && (
              <p className="text-sm text-muted-foreground">
                Selected: {selectedFile.name} ({(selectedFile.size / 1024 / 1024).toFixed(2)} MB)
              </p>
            )}
          </div>

          {/* Month and Year Selection */}
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="month">Month</Label>
              <Select value={month} onValueChange={setMonth}>
                <SelectTrigger>
                  <SelectValue placeholder="Select month" />
                </SelectTrigger>
                <SelectContent>
                  {months.map((monthName) => (
                    <SelectItem key={monthName} value={monthName}>
                      {monthName}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="year">Year</Label>
              <Select value={year} onValueChange={setYear}>
                <SelectTrigger>
                  <SelectValue placeholder="Select year" />
                </SelectTrigger>
                <SelectContent>
                  {years.map((yearValue) => (
                    <SelectItem key={yearValue} value={yearValue.toString()}>
                      {yearValue}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Upload Button */}
          <Button
            onClick={handleUpload}
            disabled={!selectedFile || !month || !year || isUploading}
            className="w-full"
          >
            {isUploading ? (
              <>
                <Upload className="h-4 w-4 mr-2 animate-spin" />
                Uploading...
              </>
            ) : (
              <>
                <Upload className="h-4 w-4 mr-2" />
                Upload Salary Data
              </>
            )}
          </Button>

          {/* Progress Bar */}
          {isUploading && (
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>Uploading...</span>
                <span>{progress}%</span>
              </div>
              <Progress value={progress} className="w-full" />
            </div>
          )}

          {/* Upload Results */}
          {uploadResult && (
            <div className="space-y-4">
              {uploadResult.success ? (
                <Alert>
                  <CheckCircle className="h-4 w-4" />
                  <AlertDescription>
                    Upload completed successfully! 
                    {uploadResult.imported_count > 0 && ` ${uploadResult.imported_count} records imported.`}
                    {uploadResult.updated_count > 0 && ` ${uploadResult.updated_count} records updated.`}
                  </AlertDescription>
                </Alert>
              ) : (
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>
                    Upload failed. Please check the errors below.
                  </AlertDescription>
                </Alert>
              )}

              {/* Errors */}
              {uploadResult.errors.length > 0 && (
                <div className="space-y-2">
                  <h4 className="font-medium text-destructive">Errors:</h4>
                  <div className="space-y-1">
                    {uploadResult.errors.map((error, index) => (
                      <p key={index} className="text-sm text-destructive bg-destructive/10 p-2 rounded">
                        {error}
                      </p>
                    ))}
                  </div>
                </div>
              )}

              {/* Warnings */}
              {uploadResult.warnings.length > 0 && (
                <div className="space-y-2">
                  <h4 className="font-medium text-yellow-600">Warnings:</h4>
                  <div className="space-y-1">
                    {uploadResult.warnings.map((warning, index) => (
                      <p key={index} className="text-sm text-yellow-600 bg-yellow-50 p-2 rounded">
                        {warning}
                      </p>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Instructions */}
      <Card>
        <CardHeader>
          <CardTitle>Instructions</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <h4 className="font-medium">Required Columns:</h4>
            <ul className="text-sm text-muted-foreground space-y-1 ml-4">
              <li>• Employee ID - Must match existing employee IDs in the system</li>
              <li>• Basic - Basic salary amount</li>
              <li>• HRA - House Rent Allowance</li>
              <li>• DA - Dearness Allowance</li>
              <li>• Conveyance - Conveyance allowance</li>
              <li>• Medical - Medical allowance</li>
              <li>• Special Allowance - Special allowance amount</li>
              <li>• PF Employee - Employee PF contribution</li>
              <li>• Professional Tax - Professional tax amount</li>
              <li>• PF Employer - Employer PF contribution</li>
              <li>• Work Days - Number of working days</li>
              <li>• Days in Month - Total days in the month</li>
              <li>• LOP Days - Loss of Pay days (optional)</li>
              <li>• Other Deductions - Any other deductions (optional)</li>
              <li>• Salary Advance - Salary advance amount (optional)</li>
            </ul>
          </div>
          <div className="space-y-2">
            <h4 className="font-medium">Notes:</h4>
            <ul className="text-sm text-muted-foreground space-y-1 ml-4">
              <li>• Employee IDs must exist in the system</li>
              <li>• If salary data already exists for the month/year, it will be updated</li>
              <li>• File size limit: 10MB</li>
              <li>• Supported formats: .xlsx, .xls</li>
            </ul>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default MonthlySalaryUpload;
