import React, { Component } from 'react'
import banner from './wr-home-top.png'
import ninjio from './ninjio_snapshot.PNG'
import './main.css'
import './rowcolumn.css'
import './Signup.css'
import appConfig from '../config/app-config.json'
import countryList from 'react-select-country-list'
import * as EmailValidator from 'email-validator'
import ReCAPTCHA from "react-google-recaptcha";

const mapStateToProps = state => {
  return { session: state.session }
}

class Signup extends Component {
  constructor(props) {
    super(props)
    this.countries = countryList().getData()
    this.countryOptions = this.countries.map((item) =>
    <option value={item.value}>{item.label}</option>
    );
    this.state = {
      firstName: '',
      lastName: '',
      age: 0,
      gender: '',
      email: '',
      affiliation: '',
      zipcode: '',
      country: 'US',
      countries: this.countries,
      userAdded: false,
      captchaCode: '',
      isLoading : false,
      responseErrors: {
        lambda: ''
      },
      errors: {
        name: '',
        email: '',
        age: '',
        zipcode: '',
        captcha: '',
        affiliation : '',
        gender : ''
      }
    };
    
    this.recaptchaRef = React.createRef();
    this.handleChange = this.handleChange.bind(this);
    this.handleSubmit = this.handleSubmit.bind(this);
  }

  handleChange(event) {
    
    // reset any error messages
    let clearErrors = {
      name:'',
      email: '',
      age: '',
      zipcode: '',
      captcha: '',
      affiliation : '',
      gender : ''
    }
    this.setState({errors : clearErrors});

    const value = event.target.value;
    const name = event.target.name;
    this.setState({
      [name]: value
    });
  }

  handleSubmit(event) {
    let knownErrors = {name: '', email: '',    age: '',    zipcode: '', captcha: '', lambda: ''}
    let submitError = false;
    let validZip = /(^\d{5}$)|(^\d{5}-\d{4}$)/.test(this.state.zipcode)
    let captchaCode = this.recaptchaRef.current.getValue();
   
    if(this.state.firstName.length === 0 || this.state.lastName.length === 0){
      knownErrors.name = 'Please enter your first and last name.';
      this.setState({errors : knownErrors});
      submitError = true;
    }
    if(!EmailValidator.validate(this.state.email)){
      knownErrors.email = 'Please enter a valid email address.';
      this.setState({errors : knownErrors});
      submitError = true;
    }
    if (this.state.affiliation.length === 0 ){
      knownErrors.affiliation = 'Please specify your affiliation.';
      this.setState({errors : knownErrors});
      submitError = true;
    }
    if (this.state.gender.length === 0 ){
      knownErrors.gender = 'Please specify your gender or indicate prefer not to say.';
      this.setState({errors : knownErrors});
      submitError = true;
    }
    if (this.state.age < 18 ){
      knownErrors.age = 'You must be at least 18 years of age to participate.';
      this.setState({errors : knownErrors});
      submitError = true;
    }
    if(!validZip){
        knownErrors.zipcode = 'You must enter a valid zipcode.';
        this.setState({errors : knownErrors});
        submitError = true;
    }
    if(captchaCode.length === 0){
        knownErrors.captcha = 'You must verify you are not a robot, please check the box below.';
        this.setState({errors : knownErrors});
        submitError = true;
    }
   if(!submitError){
      this.sendSignupInfo();
   }
    event.preventDefault();
  }

  async sendSignupInfo() {
    this.setState({isLoading : true});
    let responseError = false;
    let apiError = { lambda: ''}
    const body = {
      lastName : `${this.state.lastName}`,
      firstName : `${this.state.firstName}`,
      age : parseInt(this.state.age),
      gender : `${this.state.gender}`,
      email : `${this.state.email}`,
      affiliation : `${this.state.affiliation}`,
      zipcode : `${this.state.zipcode}`,
      country : `${this.state.country}`,
      captchaToken : `${this.recaptchaRef.current.getValue()}`
    };
    //console.log(JSON.stringify(body));

    const requestOptions = {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    };
    // About to submit reset captcha
    this.recaptchaRef.current.reset();
    fetch(appConfig.signupUri, requestOptions)
      .then(async response => {
          //console.log(response);
          const data = await response.json();
          //console.log('Response data ', data);
          // check for error response
          if (!response.ok) {
              // get error message from body or default to response status
              responseError = true;
              apiError.lambda =  (data && data['error']) || 'There was an error with your submimssion code: '+response.status;
              const error = (data && data.message) || response.status;
              this.setState({isLoading : false});
              return Promise.reject(error);
          }

          this.setState({userAdded : true});
      })
      .catch(error => {
          this.setState({responseErrors : apiError});
          console.error('There was an error!', error);
      });
    
  }

  render() {
    
    return (
      <div className="Signup">
       
        <header className="site-header">
          <img src={banner} width="100%" alt="Welcome logo" />
        </header>

        <section className="home-light">
          <div className="row column large-8">
            <h2 className="section-title-light">Welcome!</h2>
            <p className="content">
              We are thrilled to be supporting <a href="https://twitter.com/secureaerospace" target="_blank" rel="noopener noreferrer">@SecureAerospace</a> in the #AerospaceVillage at <a href="https://www.defcon.org/html/defcon-safemode/dc-safemode-index.html" target="_blank" rel="noopener noreferrer">DEF CON 28 SAFE MODE</a>.
            </p>
          </div>
        </section>

        <section className="home-dark">
          <div className="row column large-4">
            <h2 className="section-title-dark">Registration Form</h2>

            { !this.state.userAdded ? (
              <div>
                <div className="Signup-normal">Please complete the registration form below.</div>
                <div className="Signup-error">{this.state.responseErrors.lambda}</div>
                <form onSubmit={this.handleSubmit}>
              <div className="Signup-error">{this.state.errors.name}</div>
              <label>First Name:</label>
                <input className="full-width"
                  name="firstName"
                  type="text"
                  value={this.state.fname}
                  onChange={this.handleChange} />
              <br/>

              <label>Last Name:</label>
                <input className="full-width"
                  name="lastName"
                  type="text"
                  value={this.state.lname}
                  onChange={this.handleChange} />
              <br/>

              <div className="Signup-error">{this.state.errors.age}</div>
              <label>Age: </label>
                <input className="full-width"
                  name="age"
                  type="number"
                  value={this.state.age}
                  onChange={this.handleChange} />
              <br/>

              <div className="Signup-error">{this.state.errors.gender}</div>
              <label>Gender:</label>
                <select className="full-width" value={this.state.gender} name="gender" onChange={this.handleChange}>
                  <option value=""></option>
                  <option value="male">Male</option>
                  <option value="female">Female</option>
                  <option value="pnts">Prefer not to say</option>
                </select>
              <br/>

              <div className="Signup-error">{this.state.errors.email}</div>
              <label>Email:</label>
                <input className="full-width"
                  name="email"
                  type="text"
                  value={this.state.email}
                  onChange={this.handleChange} />
              <br/>

              <div className="Signup-error">{this.state.errors.affiliation}</div>
              <label>Affiliation:</label>
                <select name="affiliation" className="full-width" value={this.state.affiliation} onChange={this.handleChange}>
                <option value=""></option>
                  <option value="company">Company</option>
                  <option value="Organization">Organization</option>
                  <option value="school">School</option>
                </select>
              <br/>

              <div className="Signup-error">{this.state.errors.zipcode}</div>
              <label>Zip Code:</label>
                <input className="full-width"
                  name="zipcode"
                  type="text"
                  value={this.state.zip}
                  onChange={this.handleChange} />
              <br/>

              <label>Country:</label>
                <select className="full-width" name="country" value={this.state.country} onChange={this.handleChange}>
                  {this.countryOptions}
                </select>
              <br/><br/>

              <div className="Signup-error">{this.state.errors.captcha}</div>
              <center><ReCAPTCHA
                ref={this.recaptchaRef}
                sitekey="6LdCV7AZAAAAAHGaZRoL6JuMu9MYJ8ndtiw46Fjm"
                name="captcha"
                onChange={this.handleCaptcha} /></center>
              <br/>

              <button className="dark-button" onClick={this.handleSubmit} disabled={this.state.isLoading}>Submit</button>
              

            </form>
              </div>

              ) : (<div className="Signup-normal">Thank you for registering! You should receive an email in the next week details regarding next steps.</div>)
            }

            
          </div>

          <div className="row column large-9">
            <p className="content" style={{color: '#C69214'}}>
              <u><b>Disclaimer WARNING for California Cyber Innovation Challenge 2020 Participants:</b></u><br/>
              Coaches and students who will be participating in the California Cyber Innovation Challenge 2020 at Cal Poly on October 2nd - 4th, 2020 are NOT permitted to register for Mission Alenium at Aerospace Village, August 6th - 9th, 2020. This restriction is to ensure the integrity and fairness of the October competition. We reserve the right to disqualify any California Cyber Innovation Challenge team members or coaches found participating in this event.
            </p>
          </div>
        </section>

        <section id="introquiz" className="home-light">
          <div className="row column large-8">
            <h2 className="section-title-light">Check It Out!</h2>
            <p className="content">
              Watch an animated Ninjio video of a satellite being hacked using Social Engineering!
              <a href="https://ninjio.com/ep504" target="_blank" rel="noopener noreferrer"><img src={ninjio} alt="Ninjio video" width="500" style={{maxWidth:'100%', padding:'1em'}}/></a><br/>
              <i>Note: The video will be public from August 6th, 2020 9AM (PST) to August 9th, 2020 at 6PM (PST).</i>
              <br/><br/>
              <a className="light-button" href="https://ninjio.com/ep504" target="_blank" rel="noopener noreferrer">Watch Now!</a>
            </p>
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
    )
  }
}

export default Signup
