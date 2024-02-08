----------------------------------------------------------------------------------
-- Company: 
-- Engineer: 
-- 
-- Create Date: 2024/01/21 01:47:01
-- Design Name: 
-- Module Name: adder_subtractor_tb - Behavioral
-- Project Name: 
-- Target Devices: 
-- Tool Versions: 
-- Description: 
-- 
-- Dependencies: 
-- 
-- Revision:
-- Revision 0.01 - File Created
-- Additional Comments:
-- 
----------------------------------------------------------------------------------
--------------------------------------------------------------------------------
-- 
-- VHDL Test Bench for module: adder_subtractor.vhd
--
-- Executes an exhaustive Test Bench for mod M adder substractor
--
--------------------------------------------------------------------------------
LIBRARY ieee;
USE ieee.std_logic_1164.ALL;
USE IEEE.std_logic_arith.all;
USE ieee.std_logic_signed.all;
USE ieee.std_logic_unsigned.all;
USE ieee.numeric_std.ALL;
USE ieee.std_logic_textio.ALL;
USE std.textio.ALL;
use work.my_package.all;


ENTITY test_add_sub IS
END test_add_sub;

ARCHITECTURE behavior OF test_add_sub IS 

  -- Component Declaration for the Unit Under Test (UUT)
  COMPONENT adder_subtractor
  PORT(
    x,y : in std_logic_vector(K-1 downto 0);
    addb_sub: in std_logic;
    z: out std_logic_vector(K-1 downto 0)
    );
  END COMPONENT;

  --Inputs
  SIGNAL x, y :  std_logic_vector(K-1 downto 0) := (others=>'0');
  SIGNAL addb_sub :  std_logic;
  --Outputs
  SIGNAL z :  std_logic_vector(K-1 downto 0);

  constant DELAY : time := 100 ns;

BEGIN

  dut: adder_subtractor PORT MAP(
    x => x,
    y => y,
    addb_sub => addb_sub,
    z => z
  );

  tb_proc : PROCESS --generate values
    VARIABLE TX_LOC : LINE;
    VARIABLE TX_STR : String(1 to 4096);
    Variable M_natural: natural;
    Variable result: integer;
    BEGIN
    M_natural := ieee.std_logic_unsigned.CONV_INTEGER(M);
    
    for as in 0 to 1 loop
      if as = 0 then addb_sub <= '0'; else addb_sub <='1'; end if;
      for J in 0 to M_natural-1 loop
        for I in 0 to M_natural-1 loop
          x <= CONV_STD_LOGIC_VECTOR (I, K);
          y <= CONV_STD_LOGIC_VECTOR (J, K);
          WAIT FOR DELAY;
          IF (addb_sub = '0') THEN 
             result := (I+J) mod M_natural;
          ELSE 
             result := (I-J) mod M_natural; 
          END IF;
          IF ( result /= ieee.std_logic_unsigned.CONV_INTEGER(z) ) THEN 
            write(TX_LOC,string'("ERROR!!! X=")); write(TX_LOC, x);
            write(TX_LOC,string'("Y=")); write(TX_LOC, y);
            write(TX_LOC,string'(" mod M=")); write(TX_LOC, M);
            write(TX_LOC,string'(" is Z=")); write(TX_LOC, z);
            write(TX_LOC,string'(" instead of:")); write(TX_LOC, result);
            write(TX_LOC, string'(" "));
            write(TX_LOC,string'(" (i=")); write(TX_LOC, i);
            write(TX_LOC,string'(" j=")); write(TX_LOC, j); 
            write(TX_LOC, string'(")"));
            TX_STR(TX_LOC.all'range) := TX_LOC.all;
            Deallocate(TX_LOC);
            ASSERT (FALSE) REPORT TX_STR SEVERITY ERROR;
          END IF;  
          end loop;
      end loop;
    end loop;
    WAIT FOR DELAY;
    ASSERT (FALSE) REPORT
    "Simulation successful (not a failure).  No problems detected. "
    SEVERITY FAILURE;
   END PROCESS;

END;
