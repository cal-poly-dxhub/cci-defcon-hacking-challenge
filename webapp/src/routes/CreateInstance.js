import React, { Component } from 'react'
import './Home.css'
import request from 'request'
import appConfig from '../config/app-config.json'


class CreateInstance extends Component {
  constructor (props) {
    super(props)
    this.state = { apiStatus: 'Not called' , isLoaded: false, isClicked: false}
    this.createInstance = this.createInstance.bind(this)
  }


  createInstance(){
    // Call the API server GET /list endpoint with our JWT access token
    let url = appConfig.baseUri + this.props.action
    const options = {
      url: `${url}`,
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
        //console.log('Got a response')
        //console.log(body)
        apiResponse = JSON.parse(body)
        isLoaded = true
      }
      this.setState({ apiStatus, apiResponse , isLoaded})
    })
 } 
  render () {
    return (
     <div>
       <button onClick= {this.createInstance} > {this.props.action} instance</button>
       { (this.state.isLoaded) ? (
          <p>Result:{this.state.apiResponse['result']['InstanceId']}</p>
          ) : (
            <div></div>
          )
      }
       
     </div>
    )
  }
}

export default CreateInstance
