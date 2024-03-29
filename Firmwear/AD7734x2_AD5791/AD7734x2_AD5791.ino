


//Ardunio *DUE*code for controlling EVAL-AD7734 ADC and EVAL-AD5791 DAC
//Andrea Young
//Carlos Kometter
//James Ehrets 
//Liam A. Cohen

//3/23/2018
//Updated: 09/04/2019 by Liam A. Cohen for DAC + 2xDiff ADC box base line code

#include "SPI.h" // necessary library for SPI communication
#include <vector>
#include <math.h>
#include <DueFlashStorage.h>
DueFlashStorage dueFlashStorage;

int adc = 10; //The SPI pin for the ADC
int adc_sync[2] = {36, 24}; //24,36
int dac[4] = {50, 48, 46, 44}; //The SPI pin for the DAC
int spi[2] = {36, 24}; //24,36
int ldac = 52; //Load DAC pin for DAC. Make it LOW if not in use.12
int reset[2] = {34, 22}; //Reset on ADC 34,22
int drdy[2] = {38, 26}; // Data is ready pin on ADC ,38,26
int led = 7; //7
int data = 6; //6
int err = 11;
int eeprom = 42;
const int Noperations = 23;
String operations[Noperations] = {"NOP", "INITIALIZE", "SET", "GET_DAC", "GET_ADC", "RAMP1", "RAMP2", "BUFFER_RAMP", "BUFFER_RAMP_DIS", "RESET", "TALK", "CONVERT_TIME", "*IDN?", "*RDY?", "GET_DUNIT", "SET_DUNIT", "ADC_ZERO_SC_CAL", "ADC_CH_ZERO_SC_CAL", "ADC_CH_FULL_SC_CAL", "DAC_CH_CAL", "FULL_SCALE" , "INQUIRYOSG" , "MESSOSG"};
int initialized = 0; //address of where initialized variable is stored
int delayUnit = 0; // 0=microseconds 1=miliseconds
int adc_select = 0;

float DAC_FULL_SCALE = 10.0;
 
// Calibration constans
float OS[4] = {0.004866, 0.004866, 0.004866, 0.004866}; // offset error
float GE[4] = {0.9993023, 0.9993023, 0.9993023, 0.9993023}; // gain error
float UB[4] = {10.0 * GE[0] + OS[0], 10.0 * GE[1] + OS[1], 10.0 * GE[2] + OS[2], 10.0 * GE[3] + OS[3]};
float LB[4] = {-10.0 * GE[0] + OS[0], -10.0 * GE[1] + OS[1], -10.0 * GE[2] + OS[2], -10.0 * GE[3] + OS[3]};


std::vector<String> query_serial()
{
  char received;
  String inByte = "";
  std::vector<String> comm;
  while (received != '\r')
  {
    if (Serial.available())
    {
      received = Serial.read();
      if (received == '\n' || received == ' ')
      {}
      else if (received == ',' || received == '\r')
      {
        comm.push_back(inByte);
        inByte = "";
      }
      else
      {
        inByte += received;
      }
    }
  }
  return comm;
}


namespace std {
void __throw_bad_alloc()
{
  //Serial.println("Unable to allocate memory");
}

void __throw_length_error( char const*e )
{
  //Serial.print("Length Error :");
  //Serial.println(e);
}
};

void setup()
{
  Serial.begin(115200);
  pinMode(ldac, OUTPUT);
  digitalWrite(ldac, HIGH); //Load DAC pin for DAC. Make it LOW if not in use.
  pinMode(reset[0], OUTPUT);
  pinMode(reset[1], OUTPUT);
  pinMode(drdy[0], INPUT);  //Data ready pin for the ADC1.
  pinMode(drdy[1], INPUT);  //Data ready pin for the ADC2.
  pinMode(led, OUTPUT);  //Used for blinking indicator LED
  digitalWrite(led, HIGH);
  pinMode(data, OUTPUT);
  pinMode(eeprom, OUTPUT);
  digitalWrite(eeprom, HIGH);
  pinMode(adc_sync[0], OUTPUT);
  pinMode(adc_sync[1], OUTPUT);
  digitalWrite(adc_sync[0], HIGH);
  digitalWrite(adc_sync[1], HIGH);

  for (int i = 0; i <= 3; i++)
  {
    pinMode(dac[i], OUTPUT);
    digitalWrite(dac[i], HIGH);
  }

  digitalWrite(reset[0], HIGH);  digitalWrite(data, LOW); digitalWrite(reset[0], LOW);  digitalWrite(data, HIGH); delay(5);  digitalWrite(reset[0], HIGH);  digitalWrite(data, LOW); //Resets ADC1 on startup.
  digitalWrite(reset[1], HIGH);  digitalWrite(data, LOW); digitalWrite(reset[1], LOW);  digitalWrite(data, HIGH); delay(5);  digitalWrite(reset[1], HIGH);  digitalWrite(data, LOW); //Resets ADC2 on startup.

  SPI.begin(adc); // wake up the SPI bus for ADC
  SPI.begin(spi[0]); // wake up the SPI bus for ADC1
  SPI.begin(spi[1]); // wake up the SPI bus for ADC2

  SPI.setBitOrder(adc, MSBFIRST); //correct order for AD7734.
  SPI.setBitOrder(spi[0], MSBFIRST); //correct order for AD5764.
  SPI.setBitOrder(spi[1], MSBFIRST); //correct order for AD5764.
  SPI.setClockDivider(adc, 7);
  SPI.setClockDivider(spi[0], 84);
  SPI.setClockDivider(spi[1], 84);
  SPI.setDataMode(adc, SPI_MODE3); //This should be 3 for the AD7734
  SPI.setDataMode(spi[0], SPI_MODE1); //This should be 1 for the AD5764
  SPI.setDataMode(spi[1], SPI_MODE1); //This should be 1 for the AD5764

  // Disables DAC_SDO to avoid interference with ADC
  //  SPI.transfer(dac,1,SPI_CONTINUE);
  //  SPI.transfer(dac,0,SPI_CONTINUE);
  //  SPI.transfer(dac,1);

}

void blinker(int s) {
  digitalWrite(data, HIGH);
  delay(s);
  digitalWrite(data, LOW);
  delay(s);
}
void sos() {
  blinker(50);
  blinker(50);
  blinker(50);
  blinker(500);
  blinker(500);
  blinker(500);
  blinker(50);
  blinker(50);
  blinker(50);
}

void error()
{
  digitalWrite(err, HIGH);
  delay(3000);
  digitalWrite(err, LOW);
  delay(500);
}


int indexOfOperation(String operation)
{
  for (int index = 0; index < Noperations; index++)
  {
    if (operations[index] == operation)
    {
      return index;
    }
  }
  return 0;
}

void waitDRDY() {
  while (digitalRead(drdy[0]) == HIGH && digitalRead(drdy[1]) == HIGH ) {}
}

void resetADC() //Resets the ADC, and sets the range to default +-10 V
{
  for(int i=0; i<=1; i=i+1){
      SPI.transfer(adc, 0);
      digitalWrite(data, HIGH); digitalWrite(reset[i], HIGH); digitalWrite(reset[i], LOW); digitalWrite(reset[i], HIGH);
      digitalWrite(adc_sync[i], LOW);
      SPI.transfer(adc, 0x28);
      digitalWrite(adc_sync[i], HIGH);
      digitalWrite(adc_sync[i], LOW);
      SPI.transfer(adc, 0);
      digitalWrite(adc_sync[i], HIGH);
      digitalWrite(adc_sync[i], LOW);
      SPI.transfer(adc, 0x2A);
      digitalWrite(adc_sync[i], HIGH);
      digitalWrite(adc_sync[i], LOW);
      SPI.transfer(adc, 0);
      digitalWrite(adc_sync[i], HIGH);
  }

}

void talkADC(std::vector<String> DB)
{
  for(int i=0; i<=1; i=i+1){
      int comm;
      SPI.transfer(adc, 0);
      digitalWrite(adc_sync[i], LOW);
      comm = SPI.transfer(adc, DB[1].toInt());
      digitalWrite(adc_sync[i], HIGH);
      Serial.println(comm);
      Serial.flush();
  }
}

void writeADCConversionTime(std::vector<String> DB)
{
  int adcChannel = DB[1].toInt();
  byte cr;

  byte fw = ((byte)(((DB[2].toFloat() * 6.144 - 249) / 128) + 0.5)) | 128;
  
  if (adcChannel >= 4)
  {
    adc_select = 1;
  } 
  else
  {
    adc_select = 0;
  }
  SPI.transfer(adc, 0);
  digitalWrite(adc_sync[adc_select], LOW);
  SPI.transfer(adc, 0x30 + adcChannel);
  digitalWrite(adc_sync[adc_select], HIGH);
  digitalWrite(adc_sync[adc_select], LOW);
  SPI.transfer(adc, fw);
  digitalWrite(adc_sync[adc_select], HIGH);
  delayMicroseconds(100);
  digitalWrite(adc_sync[adc_select], LOW);
  SPI.transfer(adc, 0x70 + adcChannel);
  digitalWrite(adc_sync[adc_select], HIGH);
  digitalWrite(adc_sync[adc_select], LOW);
  cr = SPI.transfer(adc, 0); //Read back the CT register
  digitalWrite(adc_sync[adc_select], HIGH);

  int convtime = ((int)(((cr & 127) * 128 + 249) / 6.144) + 0.5);
  Serial.println(convtime);
}

float map2(float x, long in_min, long in_max, float out_min, float out_max) //float
{
  return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min;
}

int twoByteToInt(byte DB1, byte DB2) // This gives a 16 bit integer (between +/- 2^16)
{
  return ((int)((DB1 << 8) | DB2));
}


void intToTwoByte(int s, byte * DB1, byte * DB2)
{
  *DB1 = ((byte)((s >> 8) & 0xFF));
  *DB2 = ((byte)(s & 0xFF));
}


float twoByteToVoltage(byte DB1, byte DB2)
{
  int decimal;
  float voltage;

  decimal = twoByteToInt(DB1, DB2);

  if (decimal <= 32767)
  {
    voltage = decimal * 10.0 / 32767;
  }
  else
  {
    voltage = -(65536 - decimal) * 10.0 / 32768;
  }
  return voltage;
}


void voltageToTwoByte(float voltage, byte * DB1, byte * DB2)
{
  int decimal;
  if (voltage > 10 || voltage < -10)
  {
    *DB1 = 128;
    *DB2 = 0;
    error();
  }
  else if (voltage >= 0)
  {
    decimal = voltage * 32767 / 10;
  }
  else
  {
    decimal = voltage * 32768 / 10 + 65536;
  }
  intToTwoByte(decimal, DB1, DB2);
}

float getSingleReading(int adcchan)
{
  Serial.flush();
  int statusbyte = 0;
  byte o2;
  byte o3;
  int ovr;
  int indchan;
  if (adcchan <= 7)
  {
    if (adcchan >= 4)
    {
      adc_select = 1;
      indchan = adcchan - 4;
    } 
    else
    {
      adc_select = 0;
      indchan = adcchan;
    }
    SPI.transfer(adc, 0);
    digitalWrite(adc_sync[adc_select], LOW);
    SPI.transfer(adc, 0x38 + indchan); // Indicates comm register to access mode register with channel
    digitalWrite(adc_sync[adc_select], HIGH);
    digitalWrite(adc_sync[adc_select], LOW);
    SPI.transfer(adc, 0x48);          // Indicates mode register to start single convertion in dump mode
    digitalWrite(adc_sync[adc_select], HIGH);
    waitDRDY();                       // Waits until convertion finishes
    digitalWrite(adc_sync[adc_select], LOW);
    SPI.transfer(adc, 0x48 + indchan); // Indcates comm register to read data channel data register
    digitalWrite(adc_sync[adc_select], HIGH);
    digitalWrite(adc_sync[adc_select], LOW);
    statusbyte = SPI.transfer(adc, 0); // Reads Channel 'ch' status
    digitalWrite(adc_sync[adc_select], HIGH);
    digitalWrite(adc_sync[adc_select], LOW);
    o2 = SPI.transfer(adc, 0);        // Reads first byte
    digitalWrite(adc_sync[adc_select], HIGH);
    digitalWrite(adc_sync[adc_select], LOW);
    o3 = SPI.transfer(adc, 0);        // Reads second byte
    digitalWrite(adc_sync[adc_select], HIGH);
    ovr = statusbyte & 1;
    switch (ovr)
    {
      case 0:
        int decimal;
        decimal = twoByteToInt(o2, o3);
        float voltage;
        voltage = map2(decimal, 0, 65536, -10.0, 10.0);
        return voltage;
        break;

      case 1:
        return 0.0;
        break;
    }
  }
}

float readADC(byte DB)
{
  int adcChannel = DB;
  switch (adcChannel)
  {
    case 0:
      return getSingleReading(0);
      break;
    case 1:
      return getSingleReading(1);
      break;
    case 2:
      return getSingleReading(2);
      break;
    case 3:
      return getSingleReading(3);
      break;
    case 4:
      return getSingleReading(4);
      break;
    case 5:
      return getSingleReading(5);
      break;
    case 6:
      return getSingleReading(6);
      break;
    case 7:
      return getSingleReading(7);
      break;

    default:
      break;
  }
}

int threeByteToInt(byte DB1, byte DB2, byte DB3) // This gives a 16 bit integer (between +/- 2^16)
{
  return ((int)(((((DB1 & 15) << 8) | DB2) << 8) | DB3));
}

void intToThreeBytes(int decimal, byte *DB1, byte *DB2, byte *DB3)
{
  *DB1 = (byte)((decimal >> 16) | 16);
  *DB2 = (byte)((decimal >> 8) & 255);
  *DB3 = (byte)(decimal & 255);
}

float threeByteToVoltage(byte DB1, byte DB2, byte DB3)
{
  int decimal;
  float voltage;

  decimal = threeByteToInt(DB1, DB2, DB3);

  if (decimal <= 524287)
  {
    voltage = decimal * DAC_FULL_SCALE / 524287;
  }
  else
  {
    voltage = -(1048576 - decimal) * DAC_FULL_SCALE / 524288;
  }
  return voltage;
}

int voltageToDecimal(float voltage, byte *DB1, byte *DB2, byte *DB3)
{
  int decimal;
  if (voltage >= 0)
  {
    decimal = voltage * 524287 / DAC_FULL_SCALE;
  }
  else
  {
    decimal = voltage * 524288 / DAC_FULL_SCALE + 1048576;
  }
  intToThreeBytes(decimal, DB1, DB2, DB3);
}

float dacDataSend(int channelDAC, float voltage)
{
  byte b1;
  byte b2;
  byte b3;

  voltageToDecimal(voltage, &b1, &b2, &b3);
  SPI.transfer(spi[0], 0);

  digitalWrite(channelDAC, LOW);
  SPI.transfer(spi[0], b1); // send command byte to DAC
  SPI.transfer(spi[0], b2); // MS data bits, DAC2
  SPI.transfer(spi[0], b3); //LS 8 data bits, DAC2
  digitalWrite(channelDAC, HIGH);

  digitalWrite(ldac, LOW);

  digitalWrite(ldac, HIGH);

  return threeByteToVoltage(b1, b2, b3);
}

float writeDAC(int dacChannel, float voltage)
{
  switch (dacChannel)
  {
    case 0:
      return dacDataSend(dac[0], voltage / GE[0] - OS[0]);
      break;

    case 1:
      return dacDataSend(dac[1], voltage / GE[1] - OS[1]);
      break;

    case 2:
      return dacDataSend(dac[2], voltage / GE[2] - OS[2]);
      break;

    case 3:
      return dacDataSend(dac[3], voltage / GE[3] - OS[3]);
      break;

    default:
      break;
  }
}

void readingRampAvg(int adcchan, byte b1, byte b2, byte * o1, byte * o2, int count, int nReadings)
{
  Serial.flush();
  int statusbyte = 0;
  int ovr;
  byte db1;
  byte db2;
  float sum = 0;
  float avg;
  bool toSend = true;
  int indchan;
  if (adcchan <= 7)
  {
    if (adcchan >= 4)
    {
      adc_select = 1;
      indchan = adcchan - 4;
    } 
    else
    {
      adc_select = 0;
      indchan = adcchan;
    }
    for (int i = 1; i <= nReadings; i++)
    {
      SPI.transfer(adc, 0);
      digitalWrite(adc_sync[adc_select], LOW);
      SPI.transfer(adc, 0x38 + indchan); // Indicates comm register to access mode register with channel
      digitalWrite(adc_sync[adc_select], HIGH);
      digitalWrite(adc_sync[adc_select], LOW);
      SPI.transfer(adc, 0x48);          // Indicates mode register to start single convertion in dump mode
      digitalWrite(adc_sync[adc_select], HIGH);
      if (count > 0 && toSend)
      {
        Serial.write(b1);                 // Sends previous reading while it is waiting for new reading
        Serial.write(b2);
        toSend = false;
      }
      waitDRDY();                       // Waits until convertion finishes
      digitalWrite(adc_sync[adc_select], LOW);
      SPI.transfer(adc, 0x48 + indchan); // Indcates comm register to read data channel data register
      digitalWrite(adc_sync[adc_select], HIGH);
      digitalWrite(adc_sync[adc_select], LOW);
      statusbyte = SPI.transfer(adc, 0); // Reads Channel 'ch' status
      digitalWrite(adc_sync[adc_select], HIGH);
      digitalWrite(adc_sync[adc_select], LOW);
      db1 = SPI.transfer(adc, 0);        // Reads first byte
      digitalWrite(adc_sync[adc_select], HIGH);
      digitalWrite(adc_sync[adc_select], LOW);
      db2 = SPI.transfer(adc, 0);        // Reads second byte
      digitalWrite(adc_sync[adc_select], HIGH);
      ovr = statusbyte & 1;
      if (ovr) {
        break;
      }
      int decimal = twoByteToInt(db1, db2);
      float voltage = map2(decimal, 0, 65536, -10.0, 10.0);
      sum += voltage;
    }
    if (ovr)
    {
      *o1 = 128;
      *o2 = 0;
    }
    else
    {
      avg = sum / nReadings;
      int decimal = map2(avg, -10.0, 10.0, 0, 65536);
      intToTwoByte(decimal, &db1, &db2);
      *o1 = db1;
      *o2 = db2;
    }
  }
}

void rampRead(byte DB, byte b1, byte b2, byte * o1, byte * o2, int count, int nReadings )
{
  int adcChannel = DB;
  switch (adcChannel)
  {
    case 0:
      readingRampAvg(0, b1 , b2, o1, o2, count, nReadings);
      break;

    case 1:
      readingRampAvg(1, b1 , b2, o1, o2, count, nReadings);
      break;

    case 2:
      readingRampAvg(2, b1 , b2, o1, o2, count, nReadings);
      break;

    case 3:
      readingRampAvg(3, b1 , b2, o1, o2, count, nReadings);
      break;
      
    case 4:
      readingRampAvg(4, b1 , b2, o1, o2, count, nReadings);
      break;

    case 5:
      readingRampAvg(5, b1 , b2, o1, o2, count, nReadings);
      break;

    case 6:
      readingRampAvg(6, b1 , b2, o1, o2, count, nReadings);
      break;

    case 7:
      readingRampAvg(7, b1 , b2, o1, o2, count, nReadings);
      break;
    default:
      break;
  }
}

float dacDataSend_buffer(int channelDAC, float voltage)
{
  byte b1;
  byte b2;
  byte b3;

  voltageToDecimal(voltage, &b1, &b2, &b3);
  SPI.transfer(spi[0], 0);

  digitalWrite(channelDAC, LOW);
  SPI.transfer(spi[0], b1); // send command byte to DAC
  SPI.transfer(spi[0], b2); // MS data bits, DAC2
  SPI.transfer(spi[0], b3); //LS 8 data bits, DAC2
  digitalWrite(channelDAC, HIGH);

  return threeByteToVoltage(b1, b2, b3);
}

float writeDAC_buffer(int dacChannel, float voltage)
{
  switch (dacChannel)
  {
    case 0:
      return dacDataSend_buffer(dac[0], voltage / GE[0] - OS[0]);
      break;

    case 1:
      return dacDataSend_buffer(dac[1], voltage / GE[1] - OS[1]);
      break;

    case 2:
      return dacDataSend_buffer(dac[2], voltage / GE[2] - OS[2]);
      break;

    case 3:
      return dacDataSend_buffer(dac[3], voltage / GE[3] - OS[3]);
      break;

    default:
      break;
  }
}

void bufferRamp(std::vector<String> DB)
{
  String channelsDAC = DB[1];
  int NchannelsDAC = channelsDAC.length();
  String channelsADC = DB[2];
  int NchannelsADC = channelsADC.length();
  std::vector<float> vi;
  std::vector<float> vf;

  for (int i = 3; i < NchannelsDAC + 3; i++)
  {
    vi.push_back(DB[i].toFloat());
    vf.push_back(DB[i + NchannelsDAC].toFloat());
  }
  int nSteps = (DB[NchannelsDAC * 2 + 3].toInt());
  byte b1;
  byte b2;
  int count = 0;
  int overrange = 0;
  for (int i = 0; i < NchannelsDAC; i++)
  {
    if (vi[i] < LB[i] || vi[i] > UB[i] || vf[i] < LB[i] || vf[i] > UB[i]){
      overrange = 1;
    }
  }
  if (overrange == 1){
    Serial.print("VOLTAGE_OVERRANGE");
    Serial.print(LB[DB[1].toInt()],6);
    Serial.println(UB[DB[1].toInt()],6);
  }else{
    for (int j = 0; j < nSteps; j++)
    {
      for (int i = 0; i < NchannelsDAC; i++)
      {
        float v;
        v = vi[i] + (vf[i] - vi[i]) * j / (nSteps - 1);
        writeDAC_buffer(channelsDAC[i] - '0', v);
      }
      digitalWrite(ldac, LOW);
      digitalWrite(ldac, HIGH);
      if (delayUnit)
      {
        delay(DB[NchannelsDAC * 2 + 4].toInt());
      }
      else
      {
        delayMicroseconds(DB[NchannelsDAC * 2 + 4].toInt());
      }
      for (int i = 0; i < NchannelsADC; i++)
      {
        rampRead(channelsADC[i] - '0', b1, b2, &b1, &b2, count, DB[NchannelsDAC * 2 + 5].toInt());
        count += 1;
      }
      if (Serial.available())
      {
        std::vector<String> comm;
        comm = query_serial();
        if (comm[0] == "STOP")
        {
          break;
        }
      }
    }
    Serial.write(b1);
    Serial.write(b2);
    Serial.println("BUFFER_RAMP_FINISHED");
  }

}

int bufferRampDis(std::vector<String> DB)
{
  String channelsDAC = DB[1];
  int NchannelsDAC = channelsDAC.length();
  String channelsADC = DB[2];
  int NchannelsADC = channelsADC.length();
  int nAdcSteps = DB[NchannelsDAC * 2 + 6].toInt();
  int nSteps = (DB[NchannelsDAC * 2 + 3].toInt());

  if (nAdcSteps > nSteps)
  {
    Serial.println("nAdcSteps must be smaller or equal to nSteps");
    return 0;
  }

  std::vector<float> vi;
  std::vector<float> vf;
  for (int i = 3; i < NchannelsDAC + 3; i++)
  {
    vi.push_back(DB[i].toFloat());
    vf.push_back(DB[i + NchannelsDAC].toFloat());
  }
  byte b1;
  byte b2;
  int count = 0;
  int adcCount = 0;
  int overrange = 0;
  for (int i = 0; i < NchannelsDAC; i++)
  {
    if (vi[i] < LB[i] || vi[i] > UB[i] || vf[i] < LB[i] || vf[i] > UB[i]){
      overrange = 1;
    }
  }
  if (overrange == 1){
    Serial.print("VOLTAGE_OVERRANGE");
    Serial.print(LB[DB[1].toInt()],6);
    Serial.println(UB[DB[1].toInt()],6);
  }else{
    for (int j = 0; j < nSteps; j++)
    {
      for (int i = 0; i < NchannelsDAC; i++)
      {
        float v;
        v = vi[i] + (vf[i] - vi[i]) * j / (nSteps - 1);
        writeDAC_buffer(channelsDAC[i] - '0', v);
      }
      digitalWrite(ldac, LOW);
      digitalWrite(ldac, HIGH);
      if (delayUnit)
      {
        delay(DB[NchannelsDAC * 2 + 4].toInt());
      }
      else
      {
        delayMicroseconds(DB[NchannelsDAC * 2 + 4].toInt());
      }
      if (j == round(adcCount*float(nSteps-1)/float(nAdcSteps-1)))
      {
        for (int i = 0; i < NchannelsADC; i++)
        {
          rampRead(channelsADC[i] - '0', b1, b2, &b1, &b2, count, DB[NchannelsDAC * 2 + 5].toInt());
          count += 1;
        }
      adcCount += 1;
      }
      if (Serial.available())
      {
        std::vector<String> comm;
        comm = query_serial();
        if (comm[0] == "STOP")
        {
          break;
        }
      }
    }
    Serial.write(b1);
    Serial.write(b2);
    Serial.println("BUFFER_RAMP_FINISHED");
    return 0;
  }
}


void autoRamp1(std::vector<String> DB)
{
  float v1 = DB[2].toFloat();
  float v2 = DB[3].toFloat();
  int nSteps = DB[4].toInt();
  int dacChannel = DB[1].toInt();
  if (v1 < LB[dacChannel] || v1 > UB[dacChannel] || v2 < LB[dacChannel] || v2 > UB[dacChannel]){
    Serial.println("VOLTAGE_OVERRANGE");
  }else{
    for (int j = 0; j < nSteps; j++)
    {
      int timer = micros();
      writeDAC(dacChannel, v1 + (v2 - v1)*j / (nSteps - 1));
      while (micros() <= timer + DB[5].toInt());
    }
  }
}

void autoRamp2(std::vector<String> DB)
{
  float vi1 = DB[3].toFloat();
  float vi2 = DB[4].toFloat();
  float vf1 = DB[5].toFloat();
  float vf2 = DB[6].toFloat();
  int nSteps = DB[7].toInt();
  byte b1;
  byte b2;
  int dacChannel1 = DB[1].toInt();
  int dacChannel2 = DB[2].toInt();
  if (vi1 < LB[dacChannel1] || vi1 > UB[dacChannel1] || vi2 < LB[dacChannel2] || vi2 > UB[dacChannel2] || vf1 < LB[dacChannel1] || vf1 > UB[dacChannel1] || vf2 < LB[dacChannel2] || vf2 > UB[dacChannel2]){
    Serial.println("VOLTAGE_OVERRANGE");
  }else{
    for (int j = 0; j < nSteps; j++)
    {
      int timer = micros();
      writeDAC(dacChannel1, vi1 + (vf1 - vi1)*j / (nSteps - 1));
      writeDAC(dacChannel2, vi2 + (vf2 - vi2)*j / (nSteps - 1));
      while (micros() <= timer + DB[8].toInt());
    }
  }

}

void readDAC(int channelDAC)
{

  int o1;
  int o2;
  int o3;
  float voltage;
  SPI.transfer(spi[0], 0);
  digitalWrite(channelDAC, LOW);
  SPI.transfer(spi[0], 144); // send command byte to DAC
  SPI.transfer(spi[0], 0); // MS data bits, DAC2
  SPI.transfer(spi[0], 0); //LS 8 data bits, DAC2
  digitalWrite(channelDAC, HIGH);
  delayMicroseconds(1);
  digitalWrite(channelDAC, LOW);
  o1 = SPI.transfer(spi[0], 0);
  o2 = SPI.transfer(spi[0], 0);
  o3 = SPI.transfer(spi[0], 0);
  digitalWrite(channelDAC, HIGH);
  voltage = threeByteToVoltage(o1, o2, o3);
  voltage = (voltage + OS[0]) * GE[0];
  Serial.println(voltage, 5);
}

void normalMode()
{
  int attemps = 0;
  for ( int i = 0; i <= 3; i++)
  {
    int o = 0;
    dacDataSend(dac[i], 0 / GE[i] - OS[i]);
    digitalWrite(dac[i], LOW);
    SPI.transfer(spi[0], 32);
    SPI.transfer(spi[0], 0);
    SPI.transfer(spi[0], 2);//2
    digitalWrite(dac[i], HIGH);

    digitalWrite(dac[i], LOW);
    SPI.transfer(spi[0], 160);
    SPI.transfer(spi[0], 0);
    SPI.transfer(spi[0], 0);
    o = SPI.transfer(spi[0], 0);
    digitalWrite(dac[i], HIGH);
    //Serial.print(o);

    /*
      digitalWrite(dac[i],HIGH);
      delayMicroseconds(1);
      digitalWrite(dac[i],LOW);
      SPI.transfer(spi,0);
      SPI.transfer(spi,0);
      o = SPI.transfer(spi,0);
      digitalWrite(dac[i],HIGH);
    */

    if (attemps >= 5)
    {
      //Serial.print("ERROR INITIALIZING DAC");
      //Serial.println(i);
      attemps = 0;
    }
    else if (o != 2)
    {
      i = i - 1;
      attemps++;
    };
  }
}

void ID()
{
  Serial.println("DAC-ADC_AD7734-AD5780");
}

void RDY()
{
  Serial.println("READY");
}

void setUnit(int unit)
{
  if (unit == 0)
  {
    delayUnit = 0;
    Serial.println("Delay unit set to microseconds");
  }
  else if (unit == 1)
  {
    delayUnit = 1;
    Serial.println("Delay unit set to miliseconds");
  }
  else
  {
    Serial.println("Unit should be 0 (microseconds) or 1 (miliseconds)");
  }
}

void adc_zero_scale_cal()
{
  for ( int i = 0; i <= 1; i++){
    SPI.transfer(adc, 0);
    digitalWrite(adc_sync[i], LOW);
    SPI.transfer(adc, 0x38);  // Indicates comm register to access mode register
    digitalWrite(adc_sync[i], HIGH);
    digitalWrite(adc_sync[i], LOW);
    SPI.transfer(adc, 0x80);
    digitalWrite(adc_sync[i], HIGH);
    waitDRDY();
  }
}

void adc_ch_zero_scale_cal()
{
  for ( int i = 0; i <= 1; i++){
    SPI.transfer(adc, 0);
    digitalWrite(adc_sync[i], LOW);
    SPI.transfer(adc, 0x38);  // Indicates comm register to access mode register
    digitalWrite(adc_sync[i], HIGH);
    digitalWrite(adc_sync[i], LOW);
    SPI.transfer(adc, 0xC0);
    digitalWrite(adc_sync[i], HIGH);
    waitDRDY();

    digitalWrite(adc_sync[i], LOW);
    SPI.transfer(adc, 0x38 + 1); // Indicates comm register to access mode register
    digitalWrite(adc_sync[i], HIGH);
    digitalWrite(adc_sync[i], LOW);
    SPI.transfer(adc, 0xC0);
    digitalWrite(adc_sync[i], HIGH);
    waitDRDY();

    digitalWrite(adc_sync[i], LOW);
    SPI.transfer(adc, 0x38 + 2); // Indicates comm register to access mode register
    digitalWrite(adc_sync[i], HIGH);
    digitalWrite(adc_sync[i], LOW);
    SPI.transfer(adc, 0xC0);
    digitalWrite(adc_sync[i], HIGH);
    waitDRDY();

    digitalWrite(adc_sync[i], LOW);
    SPI.transfer(adc, 0x38 + 3); // Indicates comm register to access mode register
    digitalWrite(adc_sync[i], HIGH);
    digitalWrite(adc_sync[i], LOW);
    SPI.transfer(adc, 0xC0);
    digitalWrite(adc_sync[i], HIGH);
    waitDRDY();    
  }
}

void adc_ch_full_scale_cal()
{
  for ( int i = 0; i<=1; i = i+1){
    SPI.transfer(adc, 0);
    digitalWrite(adc_sync[i], LOW);
    SPI.transfer(adc, 0x38);  // Indicates comm register to access mode register
    digitalWrite(adc_sync[i], HIGH);
    digitalWrite(adc_sync[i], LOW);
    SPI.transfer(adc, 0xE0);
    digitalWrite(adc_sync[i], HIGH);
    waitDRDY();

    digitalWrite(adc_sync[i], LOW);
    SPI.transfer(adc, 0x38 + 1); // Indicates comm register to access mode register
    digitalWrite(adc_sync[i], HIGH);
    digitalWrite(adc_sync[i], LOW);
    SPI.transfer(adc, 0xE0);
    digitalWrite(adc_sync[i], HIGH);
    waitDRDY();

    digitalWrite(adc_sync[i], LOW);
    SPI.transfer(adc, 0x38 + 2); // Indicates comm register to access mode register
    digitalWrite(adc_sync[i], HIGH);
    digitalWrite(adc_sync[i], LOW);
    SPI.transfer(adc, 0xE0);
    digitalWrite(adc_sync[i], HIGH);
    waitDRDY();

    digitalWrite(adc_sync[i], LOW);
    SPI.transfer(adc, 0x38 + 3); // Indicates comm register to access mode register
    digitalWrite(adc_sync[i], HIGH);
    digitalWrite(adc_sync[i], LOW);
    SPI.transfer(adc, 0xE0);
    digitalWrite(adc_sync[i], HIGH);
    waitDRDY();
  }
}

void dac_ch_cal()
{
  for (int i = 0; i <= 3; i++)
  {
    OS[i] = 0; // offset error
    GE[i] = 1; // gain error
  }
  //set dacs to zero volts
  for (int i = 0; i <= 3; i++)
  {
    dacDataSend(dac[i], 0);
  }
  delay(1);
  //reads the offset of each channel
  for (int i = 0; i <= 3; i++)
  {
    OS[i] = readADC(i);
  }

  //set dacs to 9 volts
  float ifs = 9;
  for (int i = 0; i <= 3; i++)
  {
    dacDataSend(dac[i], ifs);
  }
  delay(1);
  //reads each channel and calculates the gain error
  for (int i = 0; i <= 3; i++)
  {
    float nfs;
    nfs = readADC(i);
    GE[i] = (nfs - OS[i]) / ifs;
  }
}

void changeosg()
{
  OS[0] = 1;
  OS[1] = 1;
  OS[2] = 1;
  OS[3] = 1;
  GE[0] = 0.5; // gain error
  GE[1] = 0.5; // gain error
  GE[2] = 0.5; // gain error
  GE[3] = 0.5; // gain error
}

void debug()
{
  delay(3000);
  delay(3000);
}

void router(std::vector<String> DB)
{
  float v;
  int operation = indexOfOperation(DB[0]);
  switch ( operation )
  {
    case 0:
      Serial.println("NOP");
      break;

    case 1:
      //    debug();
      digitalWrite(data, HIGH);
      normalMode();
      Serial.println("INITIALIZATION COMPLETE");
      digitalWrite(data, LOW);
      break;

    case 2:
      if (DB[2].toFloat() <= LB[DB[1].toInt()] || DB[2].toFloat() >= UB[DB[1].toInt()])
      {
        Serial.print("VOLTAGE_OVERRANGE");
        Serial.print(LB[DB[1].toInt()],6);
        Serial.println(UB[DB[1].toInt()],6);
        break;
      }else{
        v = writeDAC(DB[1].toInt(), DB[2].toFloat());
        Serial.print("DAC ");
        Serial.print(DB[1]);
        Serial.print(" UPDATED TO ");
        Serial.print(v, 6);
        Serial.println("V"); 
        break;
      }

    case 3:
      digitalWrite(data, HIGH);
      int channel;
      channel = dac[DB[1].toInt()];
      readDAC(channel);
      digitalWrite(data, LOW);
      break;

    case 4: // Read ADC
      digitalWrite(data, HIGH);
      v = readADC(DB[1].toInt());
      Serial.println(v, 4);
      digitalWrite(data, LOW);
      break;

    case 5:
      digitalWrite(data, HIGH);
      autoRamp1(DB);
      Serial.println("RAMP_FINISHED");
      digitalWrite(data, LOW);
      break;

    case 6:
      digitalWrite(data, HIGH);
      autoRamp2(DB);
      Serial.println("RAMP_FINISHED");
      digitalWrite(data, LOW);
      break;

    case 7: // Autoramp
      digitalWrite(data, HIGH);
      bufferRamp(DB);
      digitalWrite(data, LOW);
      break;

    case 8:
      digitalWrite(data, HIGH);
      bufferRampDis(DB);
      digitalWrite(data, LOW);
      break;

    case 9:
      resetADC();
      break;

    case 10:
      talkADC(DB);
      break;

    case 11: // Write conversion time registers
      writeADCConversionTime(DB);
      break;

    case 12: // ID
      ID();
      break;

    case 13:
      RDY();
      break;

    case 14:
      Serial.println(delayUnit);
      break;

    case 15:
      setUnit(DB[1].toInt()); // 0 = microseconds 1 = miliseconds
      break;

    case 16:
      adc_zero_scale_cal();
      Serial.println("CALIBRATION_FINISHED");
      break;

    case 17:
      adc_ch_zero_scale_cal();
      Serial.println("CALIBRATION_FINISHED");
      break;

    case 18:
      adc_ch_full_scale_cal();
      Serial.println("CALIBRATION_FINISHED");
      break;

    case 19:
      dac_ch_cal();
      Serial.println("CALIBRATION_FINISHED");

    case 20:
      DAC_FULL_SCALE = DB[1].toFloat();
      Serial.println("FULL_SCALE_UPDATED");
      break;

    case 21:
      Serial.println(OS[0]);
      Serial.println(OS[1]);
      Serial.println(OS[2]);
      Serial.println(OS[3]);
      Serial.println(GE[0]);
      Serial.println(GE[1]);
      Serial.println(GE[2]);
      Serial.println(GE[3]);
      break;
      
    case 22:
      changeosg();
      Serial.println(OS[0]);
      Serial.println(OS[1]);
      Serial.println(OS[2]);
      Serial.println(OS[3]);
      Serial.println(GE[0]);
      Serial.println(GE[1]);
      Serial.println(GE[2]);
      Serial.println(GE[3]);
      break;
      
    //default:
    //break;
  }
}

void loop()
{
  Serial.flush();
  std::vector<String> comm;

  if (dueFlashStorage.read(initialized) == 1)
  {
    normalMode();
    dueFlashStorage.write(initialized, 1);
  }

  if (Serial.available())
  {
    comm = query_serial();
    router(comm);
  }
}
