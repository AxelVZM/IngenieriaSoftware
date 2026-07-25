// src/components/common/ConfirmDialog.jsx
import React from 'react';
import {
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    Button,
    Typography,
    Box,
} from '@mui/material';
import {
    Warning as WarningIcon,
    CheckCircle as CheckCircleIcon,
    Info as InfoIcon,
    Error as ErrorIcon,
} from '@mui/icons-material';

const ConfirmDialog = ({
    open,
    onClose,
    onConfirm,
    title = '¿Confirmar acción?',
    message = '¿Estás seguro de realizar esta acción?',
    confirmText = 'Aceptar',
    cancelText = 'Cancelar',
    type = 'warning', // 'warning', 'info', 'error', 'success'
}) => {
    const handleConfirm = () => {
        onConfirm();
        onClose();
    };

    const getIcon = () => {
        switch (type) {
            case 'warning':
                return <WarningIcon sx={{ fontSize: 48, color: '#f59e0b' }} />;
            case 'error':
                return <ErrorIcon sx={{ fontSize: 48, color: '#ef4444' }} />;
            case 'success':
                return <CheckCircleIcon sx={{ fontSize: 48, color: '#10b981' }} />;
            case 'info':
            default:
                return <InfoIcon sx={{ fontSize: 48, color: '#667eea' }} />;
        }
    };

    const getButtonColor = () => {
        switch (type) {
            case 'error':
                return 'error';
            case 'success':
                return 'success';
            case 'warning':
                return 'warning';
            case 'info':
            default:
                return 'primary';
        }
    };

    return (
        <Dialog
            open={open}
            onClose={onClose}
            maxWidth="xs"
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
                    {getIcon()}
                    {title}
                </Box>
            </DialogTitle>
            <DialogContent sx={{ textAlign: 'center', pt: 2, pb: 3 }}>
                <Typography variant="body1" color="text.secondary">
                    {message}
                </Typography>
            </DialogContent>
            <DialogActions
                sx={{
                    justifyContent: 'center',
                    gap: 2,
                    pb: 3,
                    px: 3,
                }}
            >
                {cancelText && (
                    <Button
                        onClick={onClose}
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
                )}
                <Button
                    onClick={handleConfirm}
                    variant="contained"
                    color={getButtonColor()}
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

export default ConfirmDialog;
