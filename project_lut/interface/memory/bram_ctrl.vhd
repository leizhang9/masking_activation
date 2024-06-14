library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

entity bram_ctrl is
  generic (
    num_brams       : integer := 2;
    addr_width      : integer := 32;
    data_width      : integer := 16
  );
  port (
    clk             : in std_logic;
    rst             : in std_logic;
    bram_index      : in std_logic_vector(num_brams - 1 downto 0);
    addr_i          : in std_logic_vector(addr_width - 1 downto 0);
    data_i          : in std_logic_vector(data_width - 1 downto 0);
    re              : in std_logic;
    we              : in std_logic;
    data_o          : out std_logic_vector(data_width - 1 downto 0)
  );
end entity;

architecture behavioral of bram_ctrl is

  type t_vector is array (0 to num_brams - 1) of std_logic_vector(data_width - 1 downto 0);
  type states is (RESET, IDLE, START_PROC, PROC, WAIT_RDY, DONE, WR_RESP, WR_DATA);

  signal c_state : states;
  signal n_state : states;

  signal int_addr     : std_logic_vector(addr_width - 1 downto 0);
  signal addr_cnt     : unsigned(addr_width - 1 downto 0);

  signal int_bram_out : t_vector;
  signal int_bram_re  : std_logic_vector(num_brams - 1 downto 0);
  signal int_bram_we  : std_logic_vector(num_brams - 1 downto 0);
  signal int_bram_idx : std_logic_vector(num_brams - 1 downto 0);

  signal int_dut_data_i_v   : std_logic;
  signal int_dut_data_o_rdy : std_logic;

  signal int_data     : std_logic_vector(data_width - 1 downto 0);

begin

  data_o <= int_bram_out(to_integer(unsigned(bram_index)));
  int_data <= data_i;
  int_addr <= addr;

  assign : process(re, we, bram_index)
  begin
    int_bram_re <= (others => '0');
    int_bram_we <= (others => '0');
    assig_loop : for i in 0 to num_brams loop
      if to_integer(unsigned(bram_index)) = i then
        int_bram_re(i) <= re;
        int_bram_we(i) <= we;
      end if ;
    end loop ; -- assig_loop
  end process ; -- assign


  mem : for k in 0 to num_brams - 1 generate
    bram : entity work.bram_sp(rtl)
      generic map (
        width_g       => data_width,
        height_bits_g => addr_width
      )
      port map (
        clk_i  => clk,
        addr_i => int_addr,
        din_i  => int_data,
        dout_o => int_bram_out(k),
        re_i   => int_bram_re(k),
        we_i   => int_bram_we(k)
      );
  end generate ; -- mems

end architecture;
