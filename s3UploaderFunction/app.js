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

const getUploadURL = async function(userId, conversationId) {
  const actionId = parseInt(Math.random()*10000000)
  
  const s3Params = {
    Bucket: process.env.UploadBucket,
    Key:  `${userId}/${conversationId}/img/${actionId}.jpg`,
    ContentType: 'image/jpeg'
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
          "uploadURL": s3.getSignedUrl('putObject', s3Params),
          "photoFilename": `${conversationId}/img/${actionId}.jpg`
      })
    })
  })
}

// Main Lambda entry point
exports.handler = async (event) => {
  // Parse the body of the event
  const body = JSON.parse(event.body);

  // Extract userId and conversationId from the body
  const userId = body.userId;
  const conversationId = body.conversationId;

  const result = await getUploadURL(userId, conversationId)
  console.log('Result: ', result)
  return result
}