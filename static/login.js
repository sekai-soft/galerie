const passkeyIsAvailable = () => {
  document.getElementById('passkey-loading').style.display = 'none';
  document.getElementById('passkey-unavailable').style.display = 'none';
  document.getElementById('passkey-form').style.display = 'block';
}

const passkeyIsUnavailable = () => {
  document.getElementById('passkey-loading').style.display = 'none';
  document.getElementById('passkey-unavailable').style.display = 'block';
  document.getElementById('passkey-form').style.display = 'none';
}

const encode = (arrayBuffer) => {
  return String.fromCharCode.apply(null, new Uint8Array(arrayBuffer))
}

const base64Encode = (arrayBuffer) => {
  return btoa(encode(arrayBuffer));
}

const passkeyGenerateRegistrationCallback = async (response) => {
  const decoded_options = JSON.parse(response);
  const options = PublicKeyCredential.parseCreationOptionsFromJSON(decoded_options);
  const credential = await navigator.credentials.create({
    publicKey: options
  });

  // https://github.com/bitwarden/clients/issues/12060#issuecomment-2649785773
  const isPasskeyProvidedByAuthenticator =
    credential instanceof PublicKeyCredential 
      && credential.getClientExtensionResults !== PublicKeyCredential.prototype.getClientExtensionResults;
  const credentialJson = isPasskeyProvidedByAuthenticator
    ? JSON.stringify({ ...credential }, (key, value) => {
      if (key === 'rawId') {
        return base64Encode(value);
      }
      if (value instanceof AuthenticatorAttestationResponse) {
        value.attestationObject = base64Encode(value.attestationObject)
        value.clientDataJSON = base64Encode(value.clientDataJSON)
        value.authenticatorData = base64Encode(value.authenticatorData)
      }
      return value;
    })
    : JSON.stringify(credential);
  
  const passkeyVerifyRegistrationResponse = await fetch('/actions/passkey/verify_registration', {
    method: 'post',
    credentials: 'same-origin',
    body: credentialJson
  });

  if (passkeyVerifyRegistrationResponse.ok) {
    toast('Successfully registered')
    window.location.reload()
  } else {
    toast('Failed to register: ' + passkeyVerifyRegistrationResponse.error)
  }
}

if (window.PublicKeyCredential &&
  PublicKeyCredential.isUserVerifyingPlatformAuthenticatorAvailable &&
  PublicKeyCredential.isConditionalMediationAvailable) {
  // Check if user verifying platform authenticator is available.
  Promise.all([
    PublicKeyCredential.isUserVerifyingPlatformAuthenticatorAvailable(),
    PublicKeyCredential.isConditionalMediationAvailable(),
  ]).then(results => {
    if (results.every(r => r === true)) {
      passkeyIsAvailable()
    } else {
      passkeyIsUnavailable()
    }
  });
} else {
  passkeyIsUnavailable()
}
