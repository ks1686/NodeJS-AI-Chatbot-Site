declare function verify({
  signature: string,
  publicKey: string,
  data: string,
}): Promise<boolean>;

export {
  verify
};
