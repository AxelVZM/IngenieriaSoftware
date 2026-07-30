// src/components/common/DialogWrapper.jsx
import React from 'react';
import ConfirmDialog from './ConfirmDialog';
import PromptDialog from './PromptDialog';

const DialogWrapper = ({ confirmDialog, promptDialog, alertDialog, closeConfirm, closePrompt, closeAlert }) => {
    return (
        <>
            {/* Diálogo de Confirmación */}
            {confirmDialog && (
                <ConfirmDialog
                    open={confirmDialog.open}
                    onClose={closeConfirm}
                    onConfirm={confirmDialog.onConfirm}
                    title={confirmDialog.title}
                    message={confirmDialog.message}
                    confirmText={confirmDialog.confirmText}
                    type={confirmDialog.type}
                />
            )}

            {/* Diálogo de Prompt */}
            {promptDialog && (
                <PromptDialog
                    open={promptDialog.open}
                    onClose={closePrompt}
                    onConfirm={promptDialog.onConfirm}
                    title={promptDialog.title}
                    message={promptDialog.message}
                    label={promptDialog.label}
                    defaultValue={promptDialog.defaultValue}
                    placeholder={promptDialog.placeholder}
                    multiline={promptDialog.multiline}
                />
            )}

            {/* Diálogo de Alerta */}
            {alertDialog && (
                <ConfirmDialog
                    open={alertDialog.open}
                    onClose={closeAlert}
                    onConfirm={closeAlert}
                    title={alertDialog.title}
                    message={alertDialog.message}
                    confirmText="Entendido"
                    cancelText=""
                    type={alertDialog.type}
                />
            )}
        </>
    );
};

export default DialogWrapper;
