/*
  Copyright 2020 Amazon.com, Inc. or its affiliates. All Rights Reserved.
  Permission is hereby granted, free of charge, to any person obtaining a copy of this
  software and associated documentation files (the "Software"), to deal in the Software
  without restriction, including without limitation the rights to use, copy, modify,
  merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
  permit persons to whom the Software is furnished to do so.
  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
  INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
  PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
  HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
  OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
  SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
*/

'use strict'

const AWS = require('aws-sdk')
AWS.config.update({ region: process.env.AWS_REGION || 'us-east-1' })
const s3 = new AWS.S3()

const generateGetSignedUrl = async function(objectKey) {

  
  const s3Params = {
    Bucket: process.env.UploadBucket,
    Key:  objectKey,
    Expires: 60 * 2 // URL expires in 5 minutes, for example
  }

  console.log('getUploadURL: ', s3Params)
  return new Promise((resolve, reject) => {
    // Get signed URL
    resolve({
      "statusCode": 200,
      "isBase64Encoded": false,
      "headers": {
        "Access-Control-Allow-Origin": "*"
      },
      "body": JSON.stringify({
          "getURL": s3.getSignedUrl('getObject', s3Params),
      })
    })
  })
}


// Main Lambda entry point
exports.handler = async (event) => {
  // Assume userId and conversationId are passed as query parameters
  // Adjust according to how they're actually passed (e.g., in the body or another method)
  const objectKey = event.queryStringParameters.objectKey;
  const result = await generateGetSignedUrl(objectKey)
  console.log('Result: ', result)
  return result
}