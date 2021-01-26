import React, { Component } from 'react'
import banner from './wr-home-top.png'
import './main.css'
import './rowcolumn.css'
import { connect } from 'react-redux'
import cognitoUtils from '../lib/cognitoUtils'

const mapStateToProps = state => {
  return { session: state.session }
}

class Signout extends Component {
  constructor (props) {
    super(props)
    this.state = { apiStatus: 'Not called' }
  }

  componentDidMount () {
    if (this.props.session.isLoggedIn) {
      this.onSignOut()
    }
  }

  onSignOut = (e) => {
    e.preventDefault()
    cognitoUtils.signOutCognitoSession()
  }

  render () {
    return (
      <div className="Signout">

        <header className="site-header">
          <img src={banner} width="100%" alt="Welcome logo" />
        </header>

        { this.props.session.isLoggedIn ? (
          <div>
            <section className="home-light">
              <div className="row column large-6">
                <h2 className="section-title-light">Welcome!</h2>
                <br/>
                <p className="content">
                  You are signed in as:
                  <div className="section-subtitle-light">{this.props.session.user.email}</div>
                </p>
                <br/>
                <a className="light-button" href="/signout" onClick={this.onSignOut}>Sign out</a>
              </div>
            </section>
          </div>

        ) : (
          <div>
            <section className="home-light">
              <div className="row column large-6">
                <h2 className="section-title-light">Welcome!</h2>
                <br/>
                <p className="content">
                  You are not signed in.
                </p>
                <br/>
                <a className="light-button" href={cognitoUtils.getCognitoSignInUri()}>Sign in</a>
              </div>
            </section>
          </div>
        )}

        <footer className="home-dark">
          <div className="row column">
            Copyright &copy; 2020 CA Cyber - <a href="https://cci.calpoly.edu/" target="_blank" rel="noopener noreferrer">California Cybersecurity Institute</a>. All Rights Reserved.
            <br/><br/>
            <a className="menu-links" href="/">Home</a>
          </div>
        </footer>

      </div>
    )
  }
}

export default connect(mapStateToProps)(Signout)
