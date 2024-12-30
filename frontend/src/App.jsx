import React, { useState } from 'react';
import { BrowserRouter as Router, Route, Routes, Link } from 'react-router-dom';
import Home from './pages/Home';
import TeamList from './pages/TeamList';
import Team from './pages/Team';
import PlayerList from './pages/PlayerList';
import Player from './pages/Player';
import Contact from './pages/Contact';
import Guess from './pages/Guess';
import Games from './pages/Games';
import GuessTeamLogo from './pages/GuessTeamLogo';
import GuessWhoAmI from './pages/GuessWhoAmI.jsx';

function App() {
  const [menuOpen, setMenuOpen] = useState(false);

  const toggleMenu = () => {
    setMenuOpen(!menuOpen);
  };

  return (
    <Router>
      <div id="app">
        <div id="banner"></div>
        <nav>
        <div 
            className={`hamburger-menu ${menuOpen ? 'rotate' : ''}`} 
            onClick={toggleMenu}
        >
            <div></div>
            <div></div>
            <div></div>
          </div>
          <ul id="nav-bar" className={menuOpen ? 'mobile-visible' : ''}>
            <li>
              <Link to="/" onClick={() => setMenuOpen(false)}>Home</Link>
            </li>
            <li>
              <Link to="/games" onClick={() => setMenuOpen(false)}>Games</Link>
            </li>
            <li>
              <Link to="/teams" onClick={() => setMenuOpen(false)}>Teams</Link>
            </li>
            <li>
              <Link to="/players" onClick={() => setMenuOpen(false)}>Players</Link>
            </li>
            <li>
              <Link to="/contact" onClick={() => setMenuOpen(false)}>Contact</Link>
            </li>
          </ul>
        </nav>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/games">
            <Route index element={<Games />} />
            <Route path="image" element={<Guess />} />
            <Route path="team" element={<GuessTeamLogo />} />
            <Route path="whoami" element={<GuessWhoAmI />} />
          </Route>
          <Route path="/teams">
            <Route index element={<TeamList />} />
            <Route path=":teamId" element={<Team />} />
          </Route>
          <Route path="/players">
            <Route index element={<PlayerList />} />
            <Route path=":id" element={<Player />} />
          </Route>
          <Route path="/contact" element={<Contact />} />
        </Routes>
        <div className='footer'>
          <p>&copy; NBAdle</p>
          <p>All data were obtained from <a href='https://www.sportingnews.com/'>Sporting News</a></p>
        </div>
      </div>
    </Router>
  );
}

export default App;
