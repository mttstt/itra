// frontend/src/App.jsx
import React from 'react';
import { ChainEditor } from './components/ChainEditor';
import './App.css';

function App() {
    // L'ID della ChainType da modificare potrebbe venire da un URL,
    // da una selezione dell'utente, etc. Per ora, lo impostiamo fisso.
    const CHAIN_TYPE_ID_TO_EDIT = 1;

    return (
        <div className="App">
            <h1>Editor Catena Tecnologica</h1>
            <ChainEditor chainTypeId={CHAIN_TYPE_ID_TO_EDIT} />
        </div>
    );
}

export default App;
