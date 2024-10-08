import React from 'react';
import { BrowserRouter as Router, Route, Routes, Link } from 'react-router-dom';
import Home from './pages/Home';
import TeamList from './pages/TeamList';
import Team from './pages/Team';
import PlayerList from './pages/PlayerList';
import Player from './pages/Player';
import Login from './pages/Login';
import Signup from './pages/Signup';
import Guess from './pages/Guess';
import Games from './pages/Games';
import GuessTeamLogo from './pages/GuessTeamLogo';
import GuessWhoAmI from './pages/GuessWhoAmI.jsx';

function App() {
  return (
    <Router>
      <div>
        <div id='banner'></div>
        <nav>
          <ul id='nav-bar'>
            <li>
              <Link to="/">Home</Link>
            </li>
            <li>
              <Link to="/games">Games</Link>
            </li>
            <li>
              <Link to="/teams">Teams</Link>
            </li>
            <li>
              <Link to="/players">Players</Link>
            </li>
            <li>
              <Link to="/login">Login</Link>
            </li>
          </ul>
        </nav>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/games">
            <Route index element={<Games />} />
            <Route path="image" element={<Guess />} />
            <Route path='team' element={<GuessTeamLogo />} />
            <Route path='whoami' element={<GuessWhoAmI />} />
          </Route>
          <Route path="/teams">
            <Route index element={<TeamList />} />
            <Route path=":teamId" element={<Team />} />
          </Route>
          <Route path="/players" >
            <Route index element={<PlayerList />} />
            <Route path=":id" element={<Player />} />
          </Route>
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<Signup />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
