import React, { useEffect } from 'react';
import { DndContext, closestCenter } from '@dnd-kit/core';
import { useChainStore } from '../store/chainStore';
import { Palette } from './Palette';
import { TreeNode } from './TreeNode';

// ID fittizio per l'area dell'albero
const TREE_CONTAINER_ID = 'chain-tree-container';

export const ChainEditor = ({ chainTypeId }) => {
    const { chainType, loading, error, fetchInitialData, addNode, moveNode } = useChainStore();

    useEffect(() => {
        fetchInitialData(chainTypeId);
    }, [chainTypeId, fetchInitialData]);

    const handleDragEnd = (event) => {
        const { active, over } = event;

        if (!over) return;

        const isMovingNode = active.data.current?.type === 'NODE';
        const isPaletteItem = active.data.current?.type === 'PALETTE_ITEM';

        // Logica per spostare un nodo esistente
        if (isMovingNode && active.id !== over.id) {
            const nodeId = active.id;
            // Se si rilascia su un altro nodo, diventa suo figlio.
            // Se si rilascia sul contenitore, diventa un nodo radice.
            const newParentId = over.id === TREE_CONTAINER_ID ? null : over.id;
            moveNode(nodeId, newParentId);
        }

        // Logica per aggiungere un nuovo nodo dalla palette
        if (isPaletteItem) {
            const elementTypeId = active.id;
            const parentId = over.id === TREE_CONTAINER_ID ? null : over.id;
            addNode(elementTypeId, parentId, chainTypeId);
        }
    };

    if (loading) return <div>Caricamento...</div>;
    if (error) return <div>{error}</div>;
    if (!chainType) return <div>Nessuna catena tecnologica trovata.</div>;

    const renderTree = (nodes) => {
        return nodes.map(node => (
            <TreeNode key={node.id} node={node}>
                {node.children && node.children.length > 0 && renderTree(node.children)}
            </TreeNode>
        ));
    };

    return (
        <DndContext onDragEnd={handleDragEnd} collisionDetection={closestCenter}>
            <div style={{ display: 'flex', gap: '20px' }}>
                <Palette />
                <div 
                    id={TREE_CONTAINER_ID} 
                    style={{ border: '1px solid #ccc', padding: '10px', minWidth: '400px', minHeight: '500px' }}
                >
                    <h2>{chainType.nome}</h2>
                    {renderTree(chainType.nodes)}
                </div>
            </div>
        </DndContext>
    );
};
