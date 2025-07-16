import { create } from 'zustand';
import {
    getChainTypeDetails,
    getAvailableElementTypes,
    createChainNode,
    deleteChainNode,
    moveChainNode,
} from '../api/itraApi';

export const useChainStore = create((set, get) => ({
    chainType: null,
    elementTypes: [],
    loading: true,
    error: null,

    // Azioni per caricare i dati iniziali
    fetchInitialData: async (chainTypeId) => {
        set({ loading: true, error: null });
        try {
            const [chainRes, elementTypesRes] = await Promise.all([
                getChainTypeDetails(chainTypeId),
                getAvailableElementTypes(),
            ]);
            set({
                chainType: chainRes.data,
                elementTypes: elementTypesRes.data,
                loading: false,
            });
        } catch (err) {
            set({ error: 'Errore nel caricamento dei dati.', loading: false });
            console.error(err);
        }
    },

    // Azioni per manipolare l'albero
    addNode: async (elementTypeId, parentId, chainTypeId) => {
        try {
            const newNodeData = {
                element_type: elementTypeId,
                parent: parentId,
                chain_type: chainTypeId,
            };
            const res = await createChainNode(newNodeData);
            // Ricarica i dati per visualizzare l'albero aggiornato
            get().fetchInitialData(chainTypeId);
        } catch (err) {
            console.error("Errore nella creazione del nodo:", err);
        }
    },

    moveNode: async (nodeId, newParentId) => {
        try {
            await moveChainNode(nodeId, newParentId);
            // Per un'esperienza utente migliore, si potrebbe aggiornare lo stato locale
            // immediatamente e poi ricaricare, ma per semplicità ricarichiamo tutto.
            get().fetchInitialData(get().chainType.id);
        } catch (err) {
            console.error("Errore nello spostamento del nodo:", err);
        }
    },
    
    deleteNode: async (nodeId) => {
        try {
            await deleteChainNode(nodeId);
            get().fetchInitialData(get().chainType.id);
        } catch (err) {
            console.error("Errore nell'eliminazione del nodo:", err);
        }
    }
}));
