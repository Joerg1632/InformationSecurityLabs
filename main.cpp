#include <fstream>
#include <iomanip>
#include <iostream>
#include <vector>
using namespace std;
#include "main.h"

class IDEA
{
public:
	void setKey(IDEAtypes::byte in[]);          // Устанавливает 128-битный ключ
	void setPlainText(IDEAtypes::byte in[]);    // Устанавливает 64-битный блок открытого текста
	IDEAtypes::word16 invMul(IDEAtypes::word16 x);  // Вычисляет мультипликативную обратную по модулю 2^16+1
	IDEAtypes::word16 mul(IDEAtypes::word16 x, IDEAtypes::word16 y); // Мультипликация по модулю 2^16+1
	void encryption(IDEAtypes::word16 in[], IDEAtypes::word16 out[], IDEAtypes::word16 *Ek); // Основной раунд шифрования
	void enc();                                 // Шифрует plainText и расшифровывает cipherText (тест)
	void IDEATest();                            // Тест шифрования/дешифрования с выводом в файл

	void getEncRoundKey(IDEAtypes::word16 *encRoundKey); // Генерация ключей для раундов
	void getDecRoundKey(IDEAtypes::word16 *EK, IDEAtypes::word16 DK[]); // Генерация ключей для дешифрования

	IDEAtypes::byte key[16];                     // 128-битный ключ
	IDEAtypes::word16 cipherText[4];            // Шифртекст
	IDEAtypes::word16 plainText[4];             // Открытый текст
	IDEAtypes::word16 deCipherText[4];          // Дешифрованный текст
	IDEAtypes::word16 encRoundKey[52];          // 52 ключа для шифрования (8 раундов + финальный)
	IDEAtypes::word16 decRoundKey[52];          // 52 ключа для дешифрования
};

void IDEA::setPlainText(IDEAtypes::byte in[]){
	// 8 BYTE type data becomes 4 Word16 data
	int i;
	for (i=0; i<8; i+=2){
		plainText[i/2] = (in[i]<<8)+in[i+1];
	}
}

void IDEA::setKey(IDEAtypes::byte in[]){
	int i;
	for(i=0; i<16; i++){
		key[i] = in[i];
	}
	getEncRoundKey(encRoundKey);
	getDecRoundKey(encRoundKey, decRoundKey);
}

void IDEA::getEncRoundKey(IDEAtypes::word16 *encRoundKey){
	int i,j;
	for(i=0,j=0; j<8; j++){
		encRoundKey[j] = (key[i]<<8) + key[i+1];
		i+=2;
	}
	for(i=0; j<52; j++){
		i++;
		encRoundKey[i+7] = encRoundKey[i&7] << 9 | encRoundKey[(i+1) & 7] >> 7;
		encRoundKey += (i & 8);
		i &= 7;
	}
}

void IDEA::getDecRoundKey(IDEAtypes::word16 *EK, IDEAtypes::word16 DK[]){
	int i;
	IDEAtypes::word16 temp[52];
	IDEAtypes::word16 t1,t2,t3;
	IDEAtypes::word16 *p = temp + 52;
	t1 = invMul(*EK ++);
	t2 = - *EK ++;
	t3 = - *EK ++;
	*--p = invMul(*EK ++);
	*--p = t3;
	*--p = t2;
	*--p = t1;
	for(i=0; i<7; i++){
		t1 = *EK++;
		*--p = *EK++;
		*--p = t1;
		t1 = invMul(*EK++);
		t2 = - *EK ++;
		t3 = - *EK ++;
		*--p = invMul(*EK++);
		*--p = t2;
		*--p = t3;
		*--p = t1;
	}
	t1 = *EK++;
	*--p = *EK++;
	*--p = t1;
	t1 = invMul(*EK++);
	t2 = - *EK ++;
	t3 = - *EK ++;
	*--p = invMul(*EK++);
	*--p = t3;
	*--p = t2;
	*--p = t1;
	for(i=0,p=temp; i<52; i++){
		*EK++ = *p;
		*p++ = 0;
	}
}

vector<IDEAtypes::byte> ideaHash(const vector<IDEAtypes::byte>& data, IDEA& idea) {
	vector<IDEAtypes::byte> hash(8, 0); // 64-битный хеш
	IDEAtypes::byte block[8];
	IDEAtypes::word16 cipherBlock[4];

	for (size_t i = 0; i < data.size(); i += 8) {
		size_t blockSize = min<size_t>(8, data.size() - i);
		for (size_t j = 0; j < 8; j++)
			block[j] = (j < blockSize ? data[i + j] : 0);

		idea.setPlainText(block);
		idea.encryption(idea.plainText, cipherBlock, idea.encRoundKey);

		for (int j = 0; j < 4; j++) {
			hash[j*2] ^= IDEAtypes::byte(cipherBlock[j] >> 8);
			hash[j*2+1] ^= IDEAtypes::byte(cipherBlock[j] & 0xFF);
		}
	}
	return hash;
}

int countDifferentBits(const vector<IDEAtypes::byte>& a, const vector<IDEAtypes::byte>& b) {
	int count = 0;
	for (size_t i = 0; i < a.size(); i++) {
		unsigned char diff = a[i] ^ b[i];
		for (int j = 0; j < 8; j++)
			if (diff & (1 << j)) count++;
	}
	return count;
}

IDEAtypes::word16 IDEA::invMul(IDEAtypes::word16 x){
	IDEAtypes::word16 t0,t1;
	IDEAtypes::word16 q,y;
	if(x<=1){
		 return x; // 0 and 1 inverse itself
	}
	t1 = IDEAtypes::word16(0x10001L/x);
	y = IDEAtypes::word16(0x10001L%x);
	if(y == 1){
		return (1-t1) & 0xFFFF;
	}
	t0 = 1;
	do{
		q = x/y;
		x = x%y;
		t0 += q*t1;
		if(x == 1){
			return t0;
		}
		q = y/x;
		y = y%x;
		t1 += q*t0;
	}while(y!=1);
	return (1-t1) & 0xFFFF;
}

void IDEA::encryption(IDEAtypes::word16 in[], IDEAtypes::word16 out[], IDEAtypes::word16 * EK){
	IDEAtypes::word16 x1,x2,x3,x4,t1,t2;
	x1 = in[0];
	x2 = in[1];
	x3 = in[2];
	x4 = in[3];
	int r = 8;
	do{
		x1 = mul(x1, *EK++);
		x2 += *EK++;
		x3 += *EK++;
		x4 = mul(x4, *EK++);
		t2 = x1 ^ x3;
		t1 = x2 ^ x4;
		t2 = mul(t2, *EK++);
		t1 = t1 + t2;
		t1 = mul(t1, *EK++);
		t2 = t1 + t2;
		x1 ^= t1;
		x4 ^= t2;
		t2 ^= x2;
		x2 = x3 ^ t1;
		x3 = t2;
	}while(--r);
	x1 = mul(x1, *EK++);
	*out++ = x1;
	*out++ = x3 + *EK++;
	*out++ = x2 + *EK++;
	x4 = mul(x4, *EK++);
	*out = x4;
}

IDEAtypes::word16 IDEA::mul(IDEAtypes::word16 x, IDEAtypes::word16 y){
	IDEAtypes::word32 p;
	p = (IDEAtypes::word32)x * y;
	if(p){
		y = p & 0xFFFF;
		x = p >> 16;
		return (y-x) + (y<x);
	}else if (x){
		return 1-y;
	}else{
		return 1-x;
	}
}

void IDEA::enc(){
	encryption(plainText, cipherText, encRoundKey);
	encryption(cipherText, deCipherText, decRoundKey);
}

void IDEA::IDEATest(){
	ofstream fout("test.txt");
	fout<<"The input key is:"<<endl;
	int i;
	for(i=0; i<16; i++){
		fout<<hex<<int(key[i])<<" ";
	}
	fout<<endl;
	fout<<"The plain text is:"<<endl;
	for(i=0; i<4; i++){
		fout<<hex<<plainText[i]<<" ";
	}
	fout<<endl;
	fout<<"The cipherText is:"<<endl;
	for(i=0; i<4; i++){
		fout<<hex<<cipherText[i]<<" ";
	}
	fout<<endl;
	fout<<"The deCipherText is:"<<endl;
	for(i=0; i<4; i++){
		fout<<hex<<deCipherText[i]<<" ";
	}
	fout<<endl;
}

int main() {

	IDEA idea;
	IDEAtypes::byte key[16] = {0x10,0x1A,0x0C,0x0B,0x01,0x11,0x09,0x07,
							   0x32,0xA1,0xB3,0x06,0x23,0x12,0xD3,0xF1};
	idea.setKey(key);

	vector<IDEAtypes::byte> msg = {'H','e','l','l','o',' ','w','o','r','l','d'};

	auto hash1 = ideaHash(msg, idea);

	vector<IDEAtypes::byte> msg2 = msg;
	msg2[0] ^= 1;

	auto hash2 = ideaHash(msg2, idea);

	cout << "Hash1: ";
	for(auto b : hash1) cout << hex << setw(2) << setfill('0') << int(b) << " ";
	cout << "\nHash2: ";
	for(auto b : hash2) cout << hex << setw(2) << setfill('0') << int(b) << " ";
	cout << endl;

	int diffBits = countDifferentBits(hash1, hash2);
	cout << "Changed bits: " << diffBits << " out of " << hash1.size()*8 << endl;

	return 0;
}