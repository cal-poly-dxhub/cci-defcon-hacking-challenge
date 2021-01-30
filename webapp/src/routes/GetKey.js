import React, { Component } from 'react'
import request from 'request'
import appConfig from '../config/app-config.json'




class GetKey extends Component {
  constructor (props) {
    super(props)
    this.state = { apiStatus: 'Not called' , isLoaded: false, isClicked: false}
    this.getKeyFromAWS = this.getKeyFromAWS.bind(this)
  }


  getKeyFromAWS(){
    console.log(this.state)
    // Call the API server GET /list endpoint with our JWT access token
    const options = {
      url: `${appConfig.keyUri}`,
      headers: {
        Authorization: `Bearer ${this.props.session.credentials.idToken}`
      }
    }
    const element = document.createElement("a");
  
  element.click();
    console.log(this.props.session.user.userName)
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
        apiResponse = JSON.parse(body)
        isLoaded = true
        console.log(apiResponse)
        const file = new Blob([apiResponse['result']['key']], {type: 'text/plain'});
        element.href = URL.createObjectURL(file);
        element.download = this.props.session.user.userName
        document.body.appendChild(element);
        element.click(); // Required for this to work in FireFox

      }
      this.setState({ apiStatus, apiResponse , isLoaded})
    })
    
 } 
 downloadTxtFile = () => {
  
}
  render () {
    return (
      <div className="Home-details">  
       <button onClick= {this.getKeyFromAWS} >Get Public SSH Key</button>
     
          <input hidden="true" id="keyFile"></input>
       
     </div>
    )
  }
}

export default GetKey
