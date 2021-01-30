import React, { Component } from 'react'
import banner from './wr-home-top.png'
import './main.css'
import './rowcolumn.css'
import './Home.css'
import { connect } from 'react-redux'
import cognitoUtils from '../lib/cognitoUtils'
import request from 'request'
import appConfig from '../config/app-config.json'
import CreateInstance from './CreateInstance'
import GetKey from './GetKey'


const mapStateToProps = state => {
  return { session: state.session }
}

class Home extends Component {
  constructor (props) {
    super(props)
    this.state = { apiStatus: 'Not called' , isLoaded: false}
  }

  updateAWS = () => {
    this.setState({apiStatus: 'Not called' , isLoaded: false});
    this.checkAWS();
  }

 checkAWS(){
    // Call the API server GET /list endpoint with our JWT access token
    const options = {
      url: `${appConfig.apiUri}`,
      headers: {
        Authorization: `Bearer ${this.props.session.credentials.idToken}`
      }
    }
    this.setState({ apiStatus: 'Loading...' })
    request.get(options, (err, resp, body) => {
      let apiStatus, apiResponse, isLoaded
      if (err) {
        // is API server started and reachable?
        apiStatus = 'Unable to reach API'
        isLoaded = false
        console.error(apiStatus + ': ' + err)
      } else if (resp.statusCode !== 200) {
        // API returned an error
        apiStatus = 'Error response received'
        isLoaded = false
        apiResponse = body
      } else {
        apiStatus = 'Successful response received.'
        //console.log('API RESPONSE')
        //console.log(body)
        apiResponse = JSON.parse(body)
        isLoaded = true
      }
      this.setState({ apiStatus, apiResponse , isLoaded})
    })
 } 
  componentDidMount () {
    if (this.props.session.isLoggedIn) {
      this.checkAWS()
    }
  }


  render () {
    return (
      <div className="Home">

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

            <section className="home-dark">
              <div className="row column large-6">
                <h2 className="section-title-dark">Current EC2 Allocation</h2>
                <h4 className="section-subtitle-dark">Contacting AWS: {this.state.apiStatus}</h4>
                <p className="content">
                  { this.state.isLoaded ? (
                    <div>
                      <div className="Home-details"> { 
                        this.instance = this.state.apiResponse.result.map((instance, key) => <div id={key}>

                        <p className="Home-api-response">Instance Info</p>
                        <p>Instance ID: {this.state.apiResponse['result'][key]['InstanceId']}</p>
                        <p>State: {this.state.apiResponse['result'][key]['State']}</p>
                        <p>Public_DNS: {this.state.apiResponse['result'][key]['Public_DNS']}</p>
                        <p>Public_IP: {this.state.apiResponse['result'][key]['Public_IP']}</p>
                      </div>
                      )}   
                    </div>

                    <div>
                      <button onClick= {this.updateAWS} >Query Instance Status</button>
                      <GetKey session={this.props.session} action='key'></GetKey>
                      <CreateInstance session={this.props.session} action='create'></CreateInstance>
                      <CreateInstance session={this.props.session} action='stop'></CreateInstance>
                      <CreateInstance session={this.props.session} action='start'></CreateInstance>
                      <CreateInstance session={this.props.session} action='terminate'></CreateInstance>
                    </div>
                  </div>

                  ) : (
                  <div></div>
                  )}

                </p>
              </div>
            </section>

            <footer className="home-light">
              <div className="row column">
                Copyright &copy; 2020 CA Cyber - <a href="https://cci.calpoly.edu/" target="_blank" rel="noopener noreferrer">California Cybersecurity Institute</a>. All Rights Reserved.
                <br/><br/>
                <a className="menu-links" href="/">Home</a>
              </div>
            </footer>
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
              </div>
            </section>

            <footer className="home-dark">
              <div className="row column">
                Copyright &copy; 2020 CA Cyber - <a href="https://cci.calpoly.edu/" target="_blank" rel="noopener noreferrer">California Cybersecurity Institute</a>. All Rights Reserved.
                <br/><br/>
                <a className="menu-links" href="/">Home</a>
              </div>
            </footer>
          </div>
        )}

      </div>
    )
  }
}

export default connect(mapStateToProps)(Home)
