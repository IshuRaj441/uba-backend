import React, { useState, useCallback, useRef } from 'react';
import { useDropzone } from 'react-dropzone';
import {
  Box,
  Typography,
  Paper,
  Button,
  Grid,
  Card,
  CardContent,
  CardActions,
  Divider,
  CircularProgress,
  Alert,
  IconButton,
  Tooltip,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Chip,
} from '@mui/material';
import {
  CloudUpload as CloudUploadIcon,
  InsertDriveFile as FileIcon,
  PictureAsPdf as PdfIcon,
  Description as WordIcon,
  Image as ImageIcon,
  Close as CloseIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Download as DownloadIcon,
  SwapVert as ConvertIcon,
} from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';

interface FileWithPreview extends File {
  preview?: string;
  status: 'uploading' | 'converting' | 'completed' | 'error';
  error?: string;
  downloadUrl?: string;
  outputFormat?: string;
}

const SUPPORTED_FORMATS = {
  'pdf-to-docx': {
    label: 'PDF to Word',
    input: '.pdf',
    output: '.docx',
    icon: <WordIcon />,
    color: '#2b579a',
  },
  'docx-to-pdf': {
    label: 'Word to PDF',
    input: '.docx',
    output: '.pdf',
    icon: <PdfIcon />,
    color: '#d24726',
  },
  'ppt-to-pdf': {
    label: 'PowerPoint to PDF',
    input: ['.ppt', '.pptx'],
    output: '.pdf',
    icon: <PdfIcon />,
    color: '#d24726',
  },
  'ocr': {
    label: 'Image to Text (OCR)',
    input: ['.jpg', '.jpeg', '.png', '.bmp', '.tiff'],
    output: '.txt',
    icon: <ImageIcon />,
    color: '#4caf50',
  },
};

type ConversionType = keyof typeof SUPPORTED_FORMATS;

const FileConverter: React.FC = () => {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState<ConversionType>('pdf-to-docx');
  const [files, setFiles] = useState<FileWithPreview[]>([]);
  const [isConverting, setIsConverting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (!acceptedFiles.length) return;

    const newFiles = acceptedFiles.map(file => ({
      ...file,
      preview: file.type.startsWith('image/') ? URL.createObjectURL(file) : undefined,
      status: 'uploading' as const,
    }));

    setFiles(prevFiles => [...prevFiles, ...newFiles]);
    
    // Simulate upload completion
    setTimeout(() => {
      setFiles(prevFiles =>
        prevFiles.map(f => 
          newFiles.some(nf => nf.name === f.name && nf.size === f.size)
            ? { ...f, status: 'converting' as const }
            : f
        )
      );
    }, 1000);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'application/vnd.ms-powerpoint': ['.ppt'],
      'application/vnd.openxmlformats-officedocument.presentationml.presentation': ['.pptx'],
      'image/jpeg': ['.jpg', '.jpeg'],
      'image/png': ['.png'],
      'image/bmp': ['.bmp'],
      'image/tiff': ['.tiff'],
    },
    multiple: true,
  });

  const handleConvert = async () => {
    if (files.length === 0) return;
    
    setIsConverting(true);
    setError(null);

    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      // Update files with mock conversion results
      setFiles(prevFiles =>
        prevFiles.map(file => ({
          ...file,
          status: 'completed' as const,
          downloadUrl: 'https://example.com/converted-file', // In a real app, this would come from the API
          outputFormat: SUPPORTED_FORMATS[activeTab].output,
        }))
      );
      
      // Deduct credits based on conversion type
      // In a real app, this would be handled by the backend
      const creditsToDeduct = activeTab === 'ocr' ? 2 : 1;
      console.log(`Deducting ${creditsToDeduct} credits`);
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Conversion failed');
      
      // Update files with error status
      setFiles(prevFiles =>
        prevFiles.map(file => ({
          ...file,
          status: 'error' as const,
          error: 'Conversion failed. Please try again.',
        }))
      );
    } finally {
      setIsConverting(false);
    }
  };

  const handleRemoveFile = (index: number) => {
    setFiles(prevFiles => prevFiles.filter((_, i) => i !== index));
  };

  const handleDownload = (file: FileWithPreview) => {
    if (!file.downloadUrl) return;
    
    // In a real app, this would trigger the download
    const link = document.createElement('a');
    link.href = file.downloadUrl;
    link.download = `${file.name.split('.')[0]}${file.outputFormat || ''}`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleTabChange = (tab: ConversionType) => {
    setActiveTab(tab);
    setFiles([]);
  };

  // Clean up object URLs to avoid memory leaks
  React.useEffect(() => {
    return () => {
      files.forEach(file => {
        if (file.preview) {
          URL.revokeObjectURL(file.preview);
        }
      });
    };
  }, [files]);

  const formatBytes = (bytes: number, decimals = 2) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
  };

  const getFileIcon = (fileName: string) => {
    const ext = fileName.split('.').pop()?.toLowerCase();
    switch (ext) {
      case 'pdf':
        return <PdfIcon />;
      case 'docx':
      case 'doc':
        return <WordIcon />;
      case 'ppt':
      case 'pptx':
        return <WordIcon />; // Using WordIcon as a placeholder for PPT
      case 'jpg':
      case 'jpeg':
      case 'png':
      case 'bmp':
      case 'tiff':
        return <ImageIcon />;
      default:
        return <FileIcon />;
    }
  };

  const currentFormat = SUPPORTED_FORMATS[activeTab];
  const acceptedFiles = Array.isArray(currentFormat.input) 
    ? currentFormat.input.join(', ')
    : currentFormat.input;

  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        File Converter
      </Typography>
      <Typography variant="body1" color="textSecondary" paragraph>
        Convert between different file formats quickly and easily.
      </Typography>

      {/* Conversion Type Tabs */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        {(Object.keys(SUPPORTED_FORMATS) as ConversionType[]).map((key) => {
          const format = SUPPORTED_FORMATS[key];
          return (
            <Grid item key={key} xs={12} sm={6} md={4} lg={3} sx={{ display: 'flex' }}>
              <Button
                variant={activeTab === key ? 'contained' : 'outlined'}
                startIcon={format.icon}
                onClick={() => handleTabChange(key)}
                sx={{
                  textTransform: 'none',
                  borderColor: activeTab === key ? format.color : 'inherit',
                  backgroundColor: activeTab === key ? format.color : 'transparent',
                  '&:hover': {
                    backgroundColor: activeTab === key ? format.color : 'action.hover',
                  },
                }}
              >
                {format.label}
              </Button>
            </Grid>
          );
        })}
      </Grid>

      {/* File Upload Area */}
      <Paper
        {...getRootProps()}
        elevation={3}
        sx={{
          p: 4,
          mb: 4,
          border: '2px dashed',
          borderColor: isDragActive ? 'primary.main' : 'divider',
          backgroundColor: isDragActive ? 'action.hover' : 'background.paper',
          cursor: 'pointer',
          transition: 'all 0.2s ease-in-out',
          textAlign: 'center',
        }}
      >
        <input {...getInputProps()} ref={fileInputRef} />
        <CloudUploadIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
        <Typography variant="h6" gutterBottom>
          {isDragActive ? 'Drop the files here' : 'Drag & drop files here, or click to select files'}
        </Typography>
        <Typography variant="body2" color="textSecondary" paragraph>
          Supported formats: {acceptedFiles.toUpperCase()}
        </Typography>
        <Button variant="contained" color="primary">
          Select Files
        </Button>
      </Paper>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* File List */}
      {files.length > 0 && (
        <Card elevation={3} sx={{ mb: 4 }}>
          <CardContent>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="h6">
                {files.length} {files.length === 1 ? 'File' : 'Files'} to Convert
              </Typography>
              <Button
                variant="contained"
                color="primary"
                startIcon={isConverting ? <CircularProgress size={20} color="inherit" /> : <ConvertIcon />}
                onClick={handleConvert}
                disabled={isConverting}
              >
                {isConverting ? 'Converting...' : `Convert to ${currentFormat.output.toUpperCase()}`}
              </Button>
            </Box>
            
            <List>
              {files.map((file, index) => (
                <React.Fragment key={index}>
                  <ListItem
                    sx={{
                      display: 'flex',
                      flexDirection: { xs: 'column', sm: 'row' },
                      alignItems: 'flex-start',
                      py: 2,
                    }}
                  >
                    <Box display="flex" alignItems="center" flexGrow={1} width="100%">
                      <Box sx={{ mr: 2, color: 'text.secondary' }}>
                        {file.preview ? (
                          <Box
                            component="img"
                            src={file.preview}
                            alt={file.name}
                            sx={{ width: 40, height: 40, objectFit: 'cover', borderRadius: 1 }}
                          />
                        ) : (
                          <Box sx={{ fontSize: 40 }}>{getFileIcon(file.name)}</Box>
                        )}
                      </Box>
                      <Box flexGrow={1} minWidth={0}>
                        <Typography variant="subtitle2" noWrap>
                          {file.name}
                        </Typography>
                        <Box display="flex" alignItems="center" flexWrap="wrap" mt={0.5}>
                          <Typography variant="caption" color="textSecondary" sx={{ mr: 1 }}>
                            {formatBytes(file.size)}
                          </Typography>
                          {file.status === 'completed' && (
                            <Chip
                              icon={<CheckCircleIcon fontSize="small" />}
                              label="Ready to download"
                              size="small"
                              color="success"
                              variant="outlined"
                              sx={{ ml: 1 }}
                            />
                          )}
                          {file.status === 'error' && (
                            <Chip
                              icon={<ErrorIcon fontSize="small" />}
                              label={file.error || 'Error'}
                              size="small"
                              color="error"
                              variant="outlined"
                              sx={{ ml: 1 }}
                            />
                          )}
                          {file.status === 'converting' && (
                            <Chip
                              icon={<CircularProgress size={16} color="info" />}
                              label="Converting..."
                              size="small"
                              sx={{ ml: 1 }}
                            />
                          )}
                        </Box>
                      </Box>
                    </Box>
                    
                    <Box sx={{ mt: { xs: 2, sm: 0 }, display: 'flex', alignItems: 'center' }}>
                      {file.status === 'completed' && file.downloadUrl ? (
                        <Button
                          variant="outlined"
                          size="small"
                          startIcon={<DownloadIcon />}
                          onClick={() => handleDownload(file)}
                          sx={{ mr: 1 }}
                        >
                          Download
                        </Button>
                      ) : null}
                      <Tooltip title="Remove file">
                        <IconButton
                          size="small"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleRemoveFile(index);
                          }}
                          disabled={file.status === 'converting'}
                        >
                          <CloseIcon />
                        </IconButton>
                      </Tooltip>
                    </Box>
                  </ListItem>
                  {index < files.length - 1 && <Divider component="li" />}
                </React.Fragment>
              ))}
            </List>
          </CardContent>
        </Card>
      )}

      {/* Conversion Tips */}
      <Card elevation={3}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Conversion Tips
          </Typography>
          <List>
            <ListItem>
              <ListItemIcon>
                <CheckCircleIcon color="primary" />
              </ListItemIcon>
              <ListItemText 
                primary="High Quality Conversions" 
                secondary="Our conversion engine ensures your files maintain the highest possible quality."
              />
            </ListItem>
            <ListItem>
              <ListItemIcon>
                <CheckCircleIcon color="primary" />
              </ListItemIcon>
              <ListItemText 
                primary="Secure & Private" 
                secondary="Your files are automatically deleted from our servers after conversion."
              />
            </ListItem>
            <ListItem>
              <ListItemIcon>
                <CheckCircleIcon color="primary" />
              </ListItemIcon>
              <ListItemText 
                primary="No Watermarks" 
                secondary="Converted files are free of watermarks or any other limitations."
              />
            </ListItem>
          </List>
        </CardContent>
      </Card>
    </Box>
  );
};

export default FileConverter;
