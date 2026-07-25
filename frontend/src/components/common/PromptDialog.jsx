// src/components/common/PromptDialog.jsx
import React, { useState } from 'react';
import {
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    Button,
    TextField,
    Typography,
    Box,
} from '@mui/material';
import { Edit as EditIcon } from '@mui/icons-material';

const PromptDialog = ({
    open,
    onClose,
    onConfirm,
    title = 'Ingresa información',
    message = '',
    label = 'Texto',
    defaultValue = '',
    placeholder = '',
    confirmText = 'Aceptar',
    cancelText = 'Cancelar',
    multiline = false,
    required = false,
}) => {
    const [value, setValue] = useState(defaultValue);

    const handleConfirm = () => {
        if (required && !value.trim()) return;
        onConfirm(value);
        onClose();
        setValue('');
    };

    const handleClose = () => {
        onClose();
        setValue('');
    };

    return (
        <Dialog
            open={open}
            onClose={handleClose}
            maxWidth="sm"
            fullWidth
            PaperProps={{
                sx: {
                    borderRadius: 3,
                    boxShadow: '0 20px 60px rgba(0, 0, 0, 0.3)',
                },
            }}
        >
            <DialogTitle
                sx={{
                    textAlign: 'center',
                    pb: 1,
                    pt: 3,
                    fontWeight: 700,
                    fontSize: '1.25rem',
                }}
            >
                <Box display="flex" flexDirection="column" alignItems="center" gap={2}>
                    <EditIcon sx={{ fontSize: 48, color: '#667eea' }} />
                    {title}
                </Box>
            </DialogTitle>
            <DialogContent sx={{ pt: 2, pb: 3 }}>
                {message && (
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2, textAlign: 'center' }}>
                        {message}
                    </Typography>
                )}
                <TextField
                    autoFocus
                    fullWidth
                    label={label}
                    value={value}
                    onChange={(e) => setValue(e.target.value)}
                    placeholder={placeholder}
                    multiline={multiline}
                    rows={multiline ? 4 : 1}
                    variant="outlined"
                    sx={{
                        '& .MuiOutlinedInput-root': {
                            borderRadius: 2,
                        },
                    }}
                />
            </DialogContent>
            <DialogActions
                sx={{
                    justifyContent: 'center',
                    gap: 2,
                    pb: 3,
                    px: 3,
                }}
            >
                <Button
                    onClick={handleClose}
                    variant="outlined"
                    sx={{
                        borderRadius: 2,
                        textTransform: 'none',
                        fontWeight: 600,
                        px: 4,
                        borderWidth: 2,
                        '&:hover': {
                            borderWidth: 2,
                        },
                    }}
                >
                    {cancelText}
                </Button>
                <Button
                    onClick={handleConfirm}
                    variant="contained"
                    disabled={required && !value.trim()}
                    sx={{
                        borderRadius: 2,
                        textTransform: 'none',
                        fontWeight: 600,
                        px: 4,
                        boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
                        '&:hover': {
                            boxShadow: '0 6px 20px rgba(0, 0, 0, 0.2)',
                        },
                    }}
                >
                    {confirmText}
                </Button>
            </DialogActions>
        </Dialog>
    );
};

export default PromptDialog;
