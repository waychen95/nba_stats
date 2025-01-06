import React from 'react';
import { Link } from 'react-router-dom';
import '../styles/Modal.css';

function Modal({ correctPlayer, tries, onClose }) {
    return (
        <div className="modal">
            <div className="modal-content">
                <button className="modal-close" onClick={onClose}>
                    &times;
                </button>
                { tries === 1 ? <h2>🏆 Perfect! 🏆</h2> : <h2>🎉 Congratulations! 🎉</h2> }
                <p>
                    You guessed {correctPlayer.first_name} {correctPlayer.last_name} correctly in {tries} tries!
                </p>
                <Link to={`/players/${correctPlayer.id}`} className="player-link">
                    View {correctPlayer.first_name}'s Details
                </Link>
                <p>or try our other game modes <Link to="/games">here</Link>!</p>
            </div>
        </div>
    );
}

export default Modal;
