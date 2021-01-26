import React, { Component } from 'react'
import { connect } from 'react-redux'


const mapStateToProps = state => {
  return { session: state.session }
}

class ListInstancesResponse extends Component {
  constructor (data) {
    this.data = data;
  }

  render () {
    return (           
    <div> 
       {  this.data.result.map(instance => (
            <div>
            <p>Instance ID:{instance.InstancedID}</p>
            <p>State:{instance.State}</p>
            <p>Public_DNS:{instance.Public_DNS}</p>
            <p>Public_IP:{instance.Public_IP}</p>
            </div>
            ))
        } :
        <p>Instance profile loading . . .</p>
      } }
    </div>
    )
  }
}
export default ListInstancesResponse;