
library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
USE ieee.math_real.log2;
USE ieee.math_real.ceil;
USE ieee.math_real.uniform;
library work;

use work.mask_util_pkg.all;
use work.prim_ops_pkg.all;

entity activation_fsm is
	generic (
		L_g                  : positive := 32; -- fixed point width
		D_g                  : positive := 2 -- number of shares
	);
	port (
		clk_i        : in  std_ulogic;
		rst_i        : in  std_ulogic;
		dim_i        : in  std_ulogic_vector (32 - 1 downto 0);
		in_i         : in  std_ulogic_vector (L_g * D_g - 1 downto 0);
		rnd_i        : in  std_ulogic_vector (19 * L_g * (D_g - 1) - 1 downto 0);
		start_i      : in  std_ulogic;
		next_input_o : out std_ulogic;
		next_rnd_o   : out std_ulogic;
		valid_o      : out std_ulogic;
		done_o       : out std_ulogic;
		out_o        : out std_ulogic_vector (L_g * D_g - 1 downto 0);
		trn_o        : out std_ulogic_vector (L_g * D_g - 1 downto 0)

	);
end activation_fsm;

architecture rtl of activation_fsm is

	type state is (RESET, IDLE, START_ACT, WAIT_ACT, NEXT_INPUT, DONE_ACT, DONE_WAIT, WAIT_MUL, DONE);
	signal c_state : state;
	signal n_state : state;

	signal activation_start_s 	: std_ulogic;
	signal activation_done_s	 	: std_ulogic;
	signal activation_in_s			: std_ulogic_vector(L_g * D_g - 1 downto 0);
	signal activation_out_s			: std_ulogic_vector(L_g * D_g - 1 downto 0);
	signal activation_out_reg		: std_ulogic_vector(L_g * D_g - 1 downto 0);
	signal trn_share_out_s			: std_ulogic_vector(L_g * D_g - 1 downto 0);
	signal trn_share_out_reg		: std_ulogic_vector(L_g * D_g - 1 downto 0);

	signal count_reg						: unsigned(32 - 1 downto 0);
	signal count_mul_reg				: unsigned(3 downto 0);

	attribute DONT_TOUCH : string;
	attribute keep : string;

	attribute DONT_TOUCH of activation_inst : label is "true";
	
	attribute keep of activation_out_s            : signal is "true";
	attribute keep of activation_out_reg            : signal is "true";
	attribute keep of trn_share_out_s            : signal is "true";
	attribute keep of trn_share_out_reg            : signal is "true";
	

begin

	activation_in_s <= in_i;
	out_o <= activation_out_reg;
	trn_o <= trn_share_out_reg;

	out_reg : process(clk_i)
	begin
		if clk_i'event and clk_i = '1' then
			if rst_i = '1' then
				activation_out_reg	 <= (others => '0');
				trn_share_out_reg		 <= (others => '0');
			elsif c_state = DONE_WAIT then
				activation_out_reg <= activation_out_s;
				trn_share_out_reg <= trn_share_out_s;
			end if;
		end if;
	end process;

	reg : process(clk_i)
	begin
		if clk_i'event and clk_i = '1' then
			if rst_i = '1' then
				count_reg <= (others => '0');
				count_mul_reg <= (others => '0');
			elsif c_state = START_ACT then
				count_reg <= count_reg + 1;
			elsif c_state = IDLE then
				count_reg <= (others => '0');
			end if;
			if c_state = WAIT_MUL then
				count_mul_reg <= count_mul_reg + 1;
			elsif c_state = DONE_ACT then
				count_mul_reg <= (others => '0');
			end if;
		end if;
	end process;

	next_state : process(c_state, start_i, rst_i, activation_done_s, dim_i, count_reg, count_mul_reg)
	begin
		case( c_state ) is
			when RESET =>
				if rst_i = '1' then
					n_state <= RESET;
				else
					n_state <= IDLE;
				end if;
			when IDLE =>
				if start_i = '1' then
					n_state <= START_ACT;
				else
					n_state <= IDLE;
				end if;
			when START_ACT =>
				n_state <= WAIT_ACT;
			when WAIT_ACT =>
				if activation_done_s = '1' then
					n_state <= WAIT_MUL;
				else
					n_state <= WAIT_ACT;
				end if;
			when WAIT_MUL =>
				if to_integer(count_mul_reg) >= 4 then
					n_state <= DONE_WAIT;
				else
					n_state <= WAIT_MUL;
				end if;
		    when DONE_WAIT =>
		        n_state <= DONE_ACT;
			when DONE_ACT =>
                if to_integer(count_reg) >= to_integer(unsigned(dim_i)) then
                    n_state <= DONE;
                else
                    n_state <= NEXT_INPUT;
                end if;
			when NEXT_INPUT =>
				n_state <= START_ACT;
			when DONE =>
				n_state <= IDLE;
			when others =>
				n_state <= RESET;
		end case;
	end process;

	out_logic : process(c_state)
	begin
		next_input_o 				<= '0';
		next_rnd_o				  <= '0';
		valid_o 						<= '0';
		done_o 							<= '0';
		activation_start_s 	<= '0';
		next_input_o 				<= '0';
		next_rnd_o 					<= '0';
		valid_o							<= '0';
		case( c_state ) is
			when START_ACT =>
				activation_start_s 	<= '1';
			when NEXT_INPUT =>
				next_input_o 				<= '1';
				next_rnd_o 					<= '1';
			when DONE_ACT =>
				valid_o							<= '1';
			when DONE =>
				done_o 							<= '1';
			when others =>
				activation_start_s 	<= '0';
				next_input_o 				<= '0';
				next_rnd_o 					<= '0';
				valid_o 						<= '0';
				done_o 							<= '0';
		end case;
	end process;

	state_mem : process(clk_i)
	begin
		if clk_i'event and clk_i = '1' then
			if rst_i = '1' then
				c_state <= RESET;
			else
				c_state <= n_state;
			end if;
		end if;
	end process;

	activation_inst : entity work.activation
	generic map (
		L_g       => L_g,
		D_g       => D_g
	)
	port map (
		clk_i     => clk_i,
		rst_i     => rst_i,
		start_i 	=> activation_start_s,
		share_i   => activation_in_s,
		rnd_i     => rnd_i,
		done_o		=> activation_done_s,
		share_o   => activation_out_s,
		trn_share_o => trn_share_out_s
	);


end rtl;
