// src/hooks/useDialog.js
import { useState } from 'react';

export const useDialog = () => {
    const [confirmDialog, setConfirmDialog] = useState({
        open: false,
        title: '',
        message: '',
        onConfirm: null,
        type: 'warning',
        confirmText: 'Aceptar',
    });

    const [promptDialog, setPromptDialog] = useState({
        open: false,
        title: '',
        message: '',
        label: '',
        defaultValue: '',
        placeholder: '',
        multiline: false,
        onConfirm: null,
    });

    const [alertDialog, setAlertDialog] = useState({
        open: false,
        title: '',
        message: '',
        type: 'info',
    });

    const showConfirm = (options) => {
        return new Promise((resolve) => {
            setConfirmDialog({
                open: true,
                title: options.title || '¿Confirmar?',
                message: options.message || '¿Estás seguro?',
                type: options.type || 'warning',
                confirmText: options.confirmText || 'Aceptar',
                onConfirm: () => {
                    setConfirmDialog(prev => ({ ...prev, open: false }));
                    resolve(true);
                },
                onCancel: () => {
                    setConfirmDialog(prev => ({ ...prev, open: false }));
                    resolve(false);
                },
            });
        });
    };

    const showPrompt = (options) => {
        return new Promise((resolve) => {
            setPromptDialog({
                open: true,
                title: options.title || 'Ingresa información',
                message: options.message || '',
                label: options.label || 'Texto',
                defaultValue: options.defaultValue || '',
                placeholder: options.placeholder || '',
                multiline: options.multiline || false,
                onConfirm: (value) => {
                    setPromptDialog(prev => ({ ...prev, open: false }));
                    resolve(value);
                },
            });
        });
    };

    const showAlert = (message, type = 'info') => {
        setAlertDialog({
            open: true,
            title: type === 'success' ? 'Éxito' : type === 'error' ? 'Error' : 'Información',
            message,
            type,
        });
    };

    const closeConfirm = () => {
        if (confirmDialog.onCancel) {
            confirmDialog.onCancel();
        } else {
            setConfirmDialog(prev => ({ ...prev, open: false }));
        }
    };

    const closePrompt = () => setPromptDialog(prev => ({ ...prev, open: false }));
    const closeAlert = () => setAlertDialog(prev => ({ ...prev, open: false }));

    return {
        confirmDialog,
        promptDialog,
        alertDialog,
        showConfirm,
        showPrompt,
        showAlert,
        closeConfirm,
        closePrompt,
        closeAlert,
    };
};
